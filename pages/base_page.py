from playwright.sync_api import Page

from pages.cart_panel import CartPanel


def accept_cookies_when_shown(page: Page) -> None:
    """Click "Agree" on the cookie banner whenever it appears, on any page, before Playwright's next action."""
    banner = page.get_by_role("dialog", name="Privacy")
    page.add_locator_handler(banner, lambda: banner.get_by_role("button", name="Agree").click())


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.cart_button = page.get_by_role("button", name="view cart", exact=True)

    def open_cart(self) -> CartPanel:
        """Click the header cart button and return the open cart panel. Available on every page."""
        self.cart_button.click()
        return CartPanel(self.page).wait_until_open()
