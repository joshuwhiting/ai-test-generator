import sys
from pathlib import Path
from util_helpers import (
    HEADED, MAX_TESTS, MODEL, WEB_TESTS_DIR, ask_model, count_tests, failing_test_names,
    limit_tests, remove_tests, run_browser_agent, run_pytest, run_type_check,
)

TEST_FILE = WEB_TESTS_DIR / "test_web_generation.py"
IMPORT_LINE = "import re\n\nimport pytest\nfrom playwright.sync_api import Page, expect\n\n"

# Keep the end of long pytest output (the failure summary) so the fix prompt fits in the context window
MAX_ERROR_OUTPUT = 8000

# Edit this file to teach the model the right API when it invents methods
PLAYWRIGHT_CHEATSHEET = (Path(__file__).parent / "playwright_cheatsheet.md").read_text()


def explore_site(url: str) -> str:
    return run_browser_agent(
        f"""You are a QA engineer exploring a website so tests can be written for it.

1. Navigate to {url}
2. Read the page snapshot.
3. Click a few of the main links or buttons to see where they go, then go back.

When clicking, typing or hovering, set target to ONLY the element's ref from the snapshot, e.g. "e22" — not the element's text.

Then report, using the EXACT visible text from the page:
- Page title and main headings
- Links (text and where they lead)
- Buttons (text and what happens when clicked)
- Form fields (labels, placeholders) and what submitting does
- Which of the above are inside an iframe, if any
- Any other behaviour worth testing""",
        model=MODEL,
    )


def generate_tests(url: str, site_info: str) -> str:
    return ask_model(f"""You are a QA engineer. Write pytest-playwright tests for the website at {url}.

This is what was found by exploring the site:
{site_info}

Rules:
- Write at most {MAX_TESTS} tests. Pick the most important ones: page loads, key content, main navigation, main forms
- Write each test as a separate top-level function whose name starts with test_, e.g. def test_page_title(page: Page) -> None:
- Each test takes the `page: Page` fixture and starts with page.goto("{url}")
- Prefer page.get_by_role, page.get_by_text and page.get_by_label using the exact text above
- Assert with expect(...), e.g. expect(page).to_have_title(...), expect(locator).to_be_visible()
- Cover page content, navigation, and any forms or interactive elements
- Only test things listed above; do not invent elements
- Only use Playwright methods from the cheat sheet below

{PLAYWRIGHT_CHEATSHEET}

Return only the test code, no explanation, no markdown formatting, no code fences, no import statements.""")


def fix_tests(tests: str, errors: str, site_info: str) -> str:
    return ask_model(f"""You are a QA engineer. These pytest-playwright tests have failures.

What was found by exploring the site:
{site_info}

Current tests:
{tests}

Errors (from pyright type checking or pytest):
{errors[-MAX_ERROR_OUTPUT:]}

Fix ONLY the failing tests. If an element cannot be found, use a locator that matches the site info above, or remove that assertion. If a method does not exist, replace it with the correct method from the cheat sheet below.

{PLAYWRIGHT_CHEATSHEET}

Keep all passing tests exactly as they are. Return the COMPLETE test file with all tests included, no explanation, no markdown formatting, no code fences, no import statements.""")


def check_tests(tests: str) -> tuple[bool, str]:
    with open(TEST_FILE, "w") as f:
        f.write(tests)

    try:
        if count_tests(tests) == 0:
            return False, "No test functions found. Each test must be a separate top-level function whose name starts with test_."
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    # Catch invented methods/attributes before spending time launching a browser
    type_ok, output = run_type_check(TEST_FILE)
    if not type_ok:
        return False, "Type check failed:\n" + output
    return run_pytest(TEST_FILE, headed=HEADED)


def remove_failing_tests(tests: str, output: str) -> None:
    """Drop tests that still fail after the last fix attempt, keeping the passing ones."""
    removed = []
    passed = False
    while not passed:
        failing = failing_test_names(tests, output)
        if not failing:
            print(f"Could not tell which tests failed. Review {TEST_FILE} manually.")
            sys.exit(1)

        tests = remove_tests(tests, failing)
        removed += sorted(failing)
        if count_tests(tests) == 0:
            print(f"All tests failed and were removed: {', '.join(removed)}")
            sys.exit(1)

        passed, output = check_tests(tests)

    print(f"Removed {len(removed)} failing test(s): {', '.join(removed)}")
    print(f"{count_tests(tests)} passing test(s) kept in {TEST_FILE}")


# --- main ---
if len(sys.argv) != 2:
    print("Usage: python3 web_test_generator.py <url>")
    sys.exit(1)

url = sys.argv[1]

print(f"Exploring {url}...")
site_info = explore_site(url)
print(f"\nSite info:\n{site_info}\n")

print("Generating tests...")
tests = limit_tests(IMPORT_LINE + generate_tests(url, site_info), MAX_TESTS)

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    print(f"\nAttempt {attempt + 1} of {MAX_RETRIES}")

    passed, output = check_tests(tests)
    print(output)

    if passed:
        print("All tests passing!")
        break

    if attempt < MAX_RETRIES - 1:
        print("Failures detected, asking model to fix...")
        tests = limit_tests(IMPORT_LINE + fix_tests(tests, output, site_info), MAX_TESTS)
    else:
        print("Max retries reached. Removing tests that still fail...")
        remove_failing_tests(tests, output)
