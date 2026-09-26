# AI Test Generator

Automatically generates pytest tests for Python code using a local LLM via Ollama.

## Project Structure

```
ai_generator/     Agentic test generation (test_generator.py, web_test_generator.py, util_helpers.py)
pages/            Page Object Model classes
tests/code/       Generated unit tests for Python code
tests/web/        Generated website tests
pipeline/         CI: requirements.txt, run_tests.sh, jenkins/
.github/workflows GitHub Actions workflow (runs pipeline/run_tests.sh)
```

Run commands from the repo root.

## Requirements

- Python 3
- Ollama running locally with the model set in `.env` (default `qwen3.5:9b`)

## Configuration

The model is set in `.env`:

OLLAMA_MODEL=qwen3.5:9b

## Install

pip install -r pipeline/requirements.txt
playwright install chromium

## Usage

python3 ai_generator/test_generator.py your_file.py

Generated tests are written to `tests/code/test_generation.py`.

## Features

- Generates pytest tests for all functions in a file
- Auto-runs pytest after generation
- Self-corrects failing tests up to 3 attempts

## Website Tests

Explores a website with Playwright MCP, then generates and runs pytest-playwright tests for it.

### Requirements

- Node.js 18+ (runs the Playwright MCP server via npx)
- The model in `.env` must support tool calling (e.g. `ollama pull qwen3.5:9b`)

### Usage

python3 ai_generator/web_test_generator.py https://example.com

Generated tests are written to `tests/web/test_web_generation.py`.

To watch the browser, set `HEADED=true` in `.env`. To re-run the generated tests headed on their own:

python3 -m pytest tests/web --headed

To run every test: `python3 -m pytest`
