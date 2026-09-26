import sys
from pathlib import Path
from util_helpers import HEADED, WEB_TESTS_DIR, ask_model, describe_pages, drop_duplicate_imports, write_and_check_tests

TEST_FILE = WEB_TESTS_DIR / "test_e2e_generation.py"
EXAMPLE_TEST = WEB_TESTS_DIR / "test_booking_flow.py"

# Keep the end of long pytest output (the failure summary) so the fix prompt fits in the context window
MAX_ERROR_OUTPUT = 8000

PAGE_IMPORTS, PAGE_OBJECTS = describe_pages()
IMPORT_LINE = (
    "import re\nfrom datetime import date, timedelta\n\nimport pytest\n"
    "from playwright.sync_api import Page, expect\n\n" + PAGE_IMPORTS + "\n\n\n"
)
PLAYWRIGHT_CHEATSHEET = (Path(__file__).parent / "playwright_cheatsheet.md").read_text()

RULES = f"""Rules:
- Build the test from the page objects below. Call their methods; do not re-implement what a method already does
- Each method returns the page object for the page you land on; chain from that, like the example test
- The test takes the `page: Page` fixture and the `start_url: str` fixture (the starting URL); start with FindHotelPage(page).open(start_url)
- The cookie banner is accepted automatically; do not handle it
- Work out dates from date.today() with timedelta, like the example test
- If a page object has an expect_... method for a check (e.g. "check the cart/stay" -> CartPanel.expect_stay), you MUST use it; do not write your own checks for the same thing
- Otherwise assert with expect(...) on the page objects' Locator attributes. Never invent CSS selectors like .stay-dates
- If a step has no page object method, write it with Playwright from the cheat sheet and put the comment # TODO: add to page objects above it
- Write each test as a top-level function whose name starts with test_ and describes the flow

Page objects (already imported):
{PAGE_OBJECTS}

Example test using these page objects:
{EXAMPLE_TEST.read_text()}

Playwright cheat sheet (only for steps the page objects don't cover):
{PLAYWRIGHT_CHEATSHEET}"""


def generate_test(flow: str) -> str:
    return ask_model(f"""You are a QA engineer. Write a pytest end-to-end test for this user flow:

{flow}

{RULES}

Return only the test code, no explanation, no markdown formatting, no code fences, no import statements.""")


def fix_test(tests: str, errors: str, flow: str) -> str:
    return ask_model(f"""You are a QA engineer. This pytest end-to-end test is failing.

User flow it should test:
{flow}

Current test:
{tests}

Errors (from pyright type checking or pytest):
{errors[-MAX_ERROR_OUTPUT:]}

Fix the test. If a method or attribute does not exist, use one that does from the page objects below.

{RULES}

Return the COMPLETE test file, no explanation, no markdown formatting, no code fences, no import statements.""")


# --- main ---
if len(sys.argv) != 2:
    print('Usage: python3 ai_generator/e2e_test_generator.py "<describe the user flow>"')
    sys.exit(1)

flow = sys.argv[1]

print("Generating test...")
tests = IMPORT_LINE + drop_duplicate_imports(IMPORT_LINE, generate_test(flow))

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    print(f"\nAttempt {attempt + 1} of {MAX_RETRIES}")

    passed, output = write_and_check_tests(tests, TEST_FILE, headed=HEADED)
    print(output)

    if passed:
        print(f"Test passing! Saved to {TEST_FILE}")
        break

    if attempt < MAX_RETRIES - 1:
        print("Failures detected, asking model to fix...")
        tests = IMPORT_LINE + drop_duplicate_imports(IMPORT_LINE, fix_test(tests, output, flow))
    else:
        print(f"Max retries reached. Review {TEST_FILE} manually.")
        sys.exit(1)
