import ollama
import subprocess
import sys

def generate_tests(code: str, filename: str) -> str:
    module_name = filename.replace(".py", "")
    response = ollama.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "user",
                "content": f"""You are a QA engineer.
                
Given this code, write pytest tests covering:
- Happy path
- Edge cases
- Error handling

Code:
{code}

Return only the test code, no explanation, no markdown formatting, no code fences, no import statements."""
            }
        ]
    )
    tests = clean_output(response['message']['content'])
    import_line = f"from {module_name} import *\n\nimport pytest\n\n"
    return import_line + tests

def fix_tests(tests: str, errors: str) -> str:
    response = ollama.chat(
        model="gemma3:4b",
        messages=[
            {
                "role": "user",
                "content": f"""You are a QA engineer. These pytest tests have failures.

Current tests:
{tests}

Pytest errors:
{errors}

Fix ONLY the failing tests. Keep all passing tests exactly as they are. Return the COMPLETE test file with all tests included, no explanation, no markdown formatting, no code fences, no import statements."""
            }
        ]
    )
    return clean_output(response['message']['content'])

def clean_output(text: str) -> str:
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python"):]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def run_pytest() -> tuple[bool, str]:
    result = subprocess.run(
        ["python3", "-m", "pytest", "test_generation.py", "-v"],
        capture_output=True,
        text=True
    )
    passed = result.returncode == 0
    return passed, result.stdout + result.stderr

# --- main ---
filename = sys.argv[1]

with open(filename, "r") as f:
    code = f.read()

module_name = filename.replace(".py", "")
tests = generate_tests(code, filename)

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    print(f"\nAttempt {attempt + 1} of {MAX_RETRIES}")

    with open("test_generation.py", "w") as f:
        f.write(tests)

    passed, output = run_pytest()
    print(output)

    if passed:
        print("All tests passing!")
        break

    if attempt < MAX_RETRIES - 1:
        print("Failures detected, asking model to fix...")
        import_line = f"from {module_name} import *\n\nimport pytest\n\n"
        tests = import_line + fix_tests(tests, output)
    else:
        print("Max retries reached. Review test_generation.py manually.")