import re
from datetime import date

from playwright.sync_api import Page, expect


class CartPanel:
    """The side panel opened from the header cart button."""

    def __init__(self, page: Page):
        self.page = page
        self.panel = page.get_by_role("dialog", name="User Panel")
        self.cart_tab = self.panel.get_by_role("tab", name=re.compile(r"^Cart"))
        self.remove_buttons = self.panel.get_by_role("button", name="Remove")
        self.checkout_link = self.panel.get_by_role("link", name="Check out itinerary")

    def wait_until_open(self) -> "CartPanel":
        expect(self.panel).to_be_visible()
        expect(self.cart_tab).to_have_attribute("aria-selected", "true")
        return self

    def expect_stay(self, hotel: str, check_in: date, check_out: date, rooms: int = 1) -> None:
        expect(self.cart_tab).to_have_accessible_name(f"Cart ({rooms})")
        expect(self.panel.get_by_role("heading", name=hotel)).to_be_visible()
        expect(self.panel).to_contain_text(f"{check_in:%b} {check_in.day}")
        expect(self.panel).to_contain_text(str(check_out.year))
        expect(self.remove_buttons).to_have_count(rooms)
        expect(self.checkout_link).to_be_visible()
