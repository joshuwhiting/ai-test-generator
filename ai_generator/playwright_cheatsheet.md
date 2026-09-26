# Playwright Python (sync API) cheat sheet

Only use the methods listed here. If something you want is not listed, use the closest listed method.

## Finding elements

Call these on `page`, or on a locator to search inside it.

- `page.get_by_role("button", name="Sign In")` — roles: link, button, heading, textbox, checkbox, radio, combobox, img, navigation, dialog, listitem
- `page.get_by_role("heading", name="Welcome", level=1)` — headings can be filtered by level (1 = h1, 2 = h2, ...)
- `page.get_by_text("Exact text", exact=True)`
- `page.get_by_label("Email")`
- `page.get_by_placeholder("Search")`
- `page.get_by_alt_text("Logo")`
- `page.get_by_title("Close")`
- `page.get_by_test_id("submit")`
- `page.locator("#main")` — CSS selector; use this to find an element by id or class
- `locator.first`, `locator.last`, `locator.nth(0)` — pick one when several match
- `locator.filter(has_text="Sale")` — narrow a locator down

## Actions

- `page.goto(url)`, `page.go_back()`, `page.reload()`
- `locator.click()`, `locator.hover()`
- `locator.fill("text")`, `locator.press("Enter")`
- `locator.check()`, `locator.uncheck()`, `locator.select_option("value")`

## Assertions

Always assert with `expect(...)`. `expect()` takes a locator or `page` — never a string. Don't call `.inner_text()` and pass the result to `expect()`; pass the locator:

```python
expect(page.get_by_role("heading", level=3)).to_contain_text("Four Seasons Hotel Miami")   # right
expect(heading.inner_text()).to_contain_text("...")                                        # wrong: a string
```

Page:
- `expect(page).to_have_title("Exact title")`
- `expect(page).to_have_url("https://example.com/")`
- Partial matches: `expect(page).to_have_url(re.compile(r"/about"))`, `expect(page).to_have_title(re.compile("Welcome"))`

Locator:
- `to_be_visible()`, `to_be_hidden()`
- `to_be_enabled()`, `to_be_disabled()`, `to_be_editable()`, `to_be_checked()`
- `to_have_text("Exact text")`, `to_contain_text("part of text")`
- `to_have_attribute("href", "/about")`
- `to_have_value("typed text")`
- `to_have_count(3)`
- `to_have_accessible_name("Close")`
- Negate any assertion with `not_to_`, e.g. `expect(locator).not_to_be_visible()`

## iframes

Only if the site info says the element is inside an iframe:

```python
frame = page.frame_locator("iframe").first   # or .nth(i)
frame.get_by_role("button", name="Book")
```

## These do NOT exist — use the replacement

- `page.get_by_id("main")` → `page.locator("#main")`
- `page.frame_locator(...).frame(1)` → `page.frame_locator(...).nth(1)`
- `expect(locator).to_be_accessible()` → `to_be_visible()` or `to_have_accessible_name(...)`
- `expect(locator).to_exist()` → `to_be_visible()` or `to_have_count(1)`
- `expect(page).to_have_path(...)` → `to_have_url(re.compile(r"/path"))`
- `expect(locator.inner_text())` → `expect(locator)`. The type check reports this as `"str" is not assignable to "APIResponse"`
- `expect(heading).to_have_level(1)` → `expect(page.get_by_role("heading", name="...", level=1)).to_be_visible()`
