import re

from playwright.sync_api import Page, expect

from pages.stay import Stay


class CartPanel:
    """The side panel opened from the header cart button."""

    def __init__(self, page: Page):
        self.page = page
        self.panel = page.get_by_role("dialog", name="User Panel")
        self.cart_tab = self.panel.get_by_role("tab", name=re.compile(r"^Cart"))
        self.remove_buttons = self.panel.get_by_role("button", name="Remove")
        self.checkout_link = self.panel.get_by_role("link", name="Check out itinerary")

    def wait_until_open(self) -> "CartPanel":
        """Wait for the panel to show the Cart tab. open_cart() already calls this."""
        expect(self.panel).to_be_visible()
        expect(self.cart_tab).to_have_attribute("aria-selected", "true")
        return self

    def expect_stay(self, hotel: str, stay: Stay, rooms: int = 1) -> None:
        """Check the cart shows the hotel name, the booked dates and the number of rooms.

        hotel is the name shown in the cart; stay is the RatesPage's .stay (the dates that were booked).
        Example: cart.expect_stay("Four Seasons Hotel Miami", rates_page.stay, rooms=1)
        """
        expect(self.cart_tab).to_have_accessible_name(f"Cart ({rooms})")
        expect(self.panel.get_by_role("heading", name=hotel)).to_be_visible()
        expect(self.panel).to_contain_text(f"{stay.check_in:%b} {stay.check_in.day}")
        expect(self.panel).to_contain_text(str(stay.check_out.year))
        expect(self.remove_buttons).to_have_count(rooms)
        expect(self.checkout_link).to_be_visible()
