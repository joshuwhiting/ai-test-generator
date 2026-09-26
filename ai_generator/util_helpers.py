import ast
import asyncio
import os
import re
import subprocess
from pathlib import Path

import ollama
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
CODE_TESTS_DIR = ROOT / "tests" / "code"
WEB_TESTS_DIR = ROOT / "tests" / "web"

load_dotenv(ROOT / ".env")

_model = os.getenv("OLLAMA_MODEL")
if not _model:
    raise RuntimeError("OLLAMA_MODEL is not set. Add it to the .env file, e.g. OLLAMA_MODEL=qwen3.5:9b")
MODEL: str = _model

# Context window in tokens: must fit the prompt AND the model's reply. Ollama's default (4096) cuts off long test files.
# Every call uses the same value so Ollama doesn't reload the model between calls.
NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "16384"))
OLLAMA_OPTIONS = {"num_ctx": NUM_CTX}

MAX_TESTS = int(os.getenv("MAX_TESTS", "10"))

HEADED = os.getenv("HEADED", "false").lower() == "true"

PLAYWRIGHT_SERVER = StdioServerParameters(
    command="npx",
    args=["@playwright/mcp@latest"] + ([] if HEADED else ["--headless"]),
)

# Only expose the tools needed to explore a site; fewer tools keeps small models on track
BROWSER_TOOLS = {
    "browser_navigate",
    "browser_navigate_back",
    "browser_snapshot",
    "browser_click",
    "browser_type",
    "browser_hover",
}

MAX_TOOL_OUTPUT = 8000

# Tool arguments the model may not use: "filename" makes browser_snapshot write to disk instead of returning the page
BLOCKED_TOOL_ARGS = {"filename"}


def clean_output(text: str) -> str:
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python"):]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def ask_model(prompt: str) -> str:
    """Send a single prompt to the model and return its cleaned-up reply."""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        think=False,
        options=OLLAMA_OPTIONS,
    )
    if response.done_reason == "length":
        print(f"Warning: the model's reply was cut off at the {NUM_CTX}-token context limit. "
              f"Increase OLLAMA_NUM_CTX in .env.")
    return clean_output(response.message.content or "")


def run_pytest(test_file: Path, headed: bool = False) -> tuple[bool, str]:
    result = subprocess.run(
        ["python3", "-m", "pytest", str(test_file), "-v"] + (["--headed"] if headed else []),
        capture_output=True,
        text=True,
        cwd=ROOT
    )
    passed = result.returncode == 0
    return passed, result.stdout + result.stderr


def run_type_check(file: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["npx", "-y", "pyright", str(file)],
        capture_output=True,
        text=True,
        cwd=ROOT
    )
    passed = result.returncode == 0
    return passed, result.stdout + result.stderr


def _test_functions(source: str) -> list[ast.FunctionDef]:
    tree = ast.parse(source)
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test")]


def failing_test_names(source: str, output: str) -> set[str] | None:
    """Names of the tests blamed in pyright or pytest output.

    Returns None if a failure can't be pinned to a test (e.g. a syntax error or module-level error).
    """
    try:
        functions = _test_functions(source)
    except SyntaxError:
        return None

    names = set()

    # Type check errors look like "file.py:73:25 - error: ..." -> blame the test function containing line 73
    for line_no in (int(n) for n in re.findall(r":(\d+):\d+ - error", output)):
        owner = next((f for f in functions if f.lineno <= line_no <= (f.end_lineno or f.lineno)), None)
        if owner is None:
            return None
        names.add(owner.name)

    # Pytest failures look like "FAILED tests/web/test_x.py::TestClass::test_name[chromium] - ..."
    for node_id in re.findall(r"^(?:FAILED|ERROR) (\S+::\S+)", output, re.MULTILINE):
        names.add(node_id.split("::")[-1].split("[")[0])

    if "ERROR collecting" in output or "errors during collection" in output:
        return None

    return names


def remove_tests(source: str, names: set[str]) -> str:
    """Remove the named test functions (including their decorators) from source."""
    lines = source.splitlines(keepends=True)
    for f in sorted(_test_functions(source), key=lambda f: f.lineno, reverse=True):
        if f.name in names:
            start = min([d.lineno for d in f.decorator_list] + [f.lineno]) - 1
            del lines[start:f.end_lineno]
    return "".join(lines)


def limit_tests(source: str, max_tests: int) -> str:
    """Keep only the first max_tests test functions, in case the model writes more than asked."""
    try:
        extra = {f.name for f in sorted(_test_functions(source), key=lambda f: f.lineno)[max_tests:]}
    except SyntaxError:
        return source  # let the type check / pytest report it
    if extra:
        print(f"Model wrote more than {max_tests} tests; dropping: {', '.join(sorted(extra))}")
    return remove_tests(source, extra)


def count_tests(source: str) -> int:
    """Number of test functions in source. Raises SyntaxError if source doesn't parse."""
    return len(_test_functions(source))


def _without_blocked_args(schema: dict) -> dict:
    properties = {k: v for k, v in schema.get("properties", {}).items() if k not in BLOCKED_TOOL_ARGS}
    required = [r for r in schema.get("required", []) if r not in BLOCKED_TOOL_ARGS]
    return {**schema, "properties": properties, "required": required}


async def _run_browser_agent(prompt: str, model: str, max_steps: int) -> str:
    async with stdio_client(PLAYWRIGHT_SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_tools = (await session.list_tools()).tools
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": _without_blocked_args(t.input_schema),
                    },
                }
                for t in mcp_tools
                if t.name in BROWSER_TOOLS
            ]

            client = ollama.AsyncClient()
            messages: list[ollama.Message] = [ollama.Message(role="user", content=prompt)]

            for step in range(max_steps):
                response = await client.chat(
                    model=model,
                    messages=messages,
                    tools=tools,
                    think=False,
                    options=OLLAMA_OPTIONS,
                )
                msg = response.message
                messages.append(msg)

                if not msg.tool_calls:
                    return msg.content or ""

                for call in msg.tool_calls:
                    print(f"  [browser] {call.function.name} {call.function.arguments}")
                    args = {k: v for k, v in call.function.arguments.items() if k not in BLOCKED_TOOL_ARGS}
                    result = await session.call_tool(call.function.name, args)
                    text = "\n".join(c.text for c in result.content if c.type == "text")
                    # Other tools save the page snapshot to a file; fetch it inline so the model can see the page
                    if call.function.name != "browser_snapshot":
                        snapshot = await session.call_tool("browser_snapshot", {})
                        text += "\n" + "\n".join(c.text for c in snapshot.content if c.type == "text")
                    messages.append(ollama.Message(
                        role="tool",
                        content=text[:MAX_TOOL_OUTPUT],
                        tool_name=call.function.name,
                    ))

            # Out of steps: ask for a final answer without tools
            messages.append(ollama.Message(role="user", content="Stop browsing and give your final answer now."))
            response = await client.chat(model=model, messages=messages, think=False, options=OLLAMA_OPTIONS)
            return response.message.content or ""


def run_browser_agent(prompt: str, model: str = MODEL, max_steps: int = 15) -> str:
    return asyncio.run(_run_browser_agent(prompt, model, max_steps))
