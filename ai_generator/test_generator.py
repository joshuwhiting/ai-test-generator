import sys
from util_helpers import CODE_TESTS_DIR, MAX_TESTS, ask_model, limit_tests, run_pytest

TEST_FILE = CODE_TESTS_DIR / "test_generation.py"

def generate_tests(code: str, filename: str) -> str:
    module_name = filename.replace(".py", "")
    tests = ask_model(f"""You are a QA engineer.

Given this code, write pytest tests covering:
- Happy path
- Edge cases
- Error handling

Write at most {MAX_TESTS} tests, each as a separate function whose name starts with test_.

Code:
{code}

Return only the test code, no explanation, no markdown formatting, no code fences, no import statements.""")
    import_line = f"from {module_name} import *\n\nimport pytest\n\n"
    return import_line + tests

def fix_tests(tests: str, errors: str) -> str:
    return ask_model(f"""You are a QA engineer. These pytest tests have failures.

Current tests:
{tests}

Pytest errors:
{errors}

Fix ONLY the failing tests. Keep all passing tests exactly as they are. Return the COMPLETE test file with all tests included, no explanation, no markdown formatting, no code fences, no import statements.""")

# --- main ---
filename = sys.argv[1]

with open(filename, "r") as f:
    code = f.read()

module_name = filename.replace(".py", "")
tests = limit_tests(generate_tests(code, filename), MAX_TESTS)

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    print(f"\nAttempt {attempt + 1} of {MAX_RETRIES}")

    with open(TEST_FILE, "w") as f:
        f.write(tests)

    passed, output = run_pytest(TEST_FILE)
    print(output)

    if passed:
        print("All tests passing!")
        break

    if attempt < MAX_RETRIES - 1:
        print("Failures detected, asking model to fix...")
        import_line = f"from {module_name} import *\n\nimport pytest\n\n"
        tests = limit_tests(import_line + fix_tests(tests, output), MAX_TESTS)
    else:
        print(f"Max retries reached. Review {TEST_FILE} manually.")
        sys.exit(1)