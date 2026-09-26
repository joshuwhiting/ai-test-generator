import re

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.stay import Stay
from pages.things_to_do_page import ThingsToDoPage


class RatesPage(BasePage):
    """A hotel's accommodations page listing rooms and rates for the chosen dates."""

    def __init__(self, page, stay: Stay):
        super().__init__(page)
        self.stay = stay
        self.heading = page.get_by_role("heading", name=re.compile(r"Accommodations$"), level=1)
        self.add_to_cart_buttons = page.get_by_role("button", name="Add to Cart")

    def wait_until_loaded(self) -> "RatesPage":
        # Match this stay's dates so a previous search's results aren't mistaken for this one
        expect(self.page).to_have_url(re.compile(rf"checkInDate={self.stay.check_in.isoformat()}"), timeout=30000)
        expect(self.heading).to_be_visible(timeout=30000)
        return self

    def has_rooms(self, timeout: float = 20000) -> bool:
        """True if any room can be added to the cart. Rooms load slowly and an empty result shows no message,
        so this waits up to timeout ms for the first one."""
        try:
            expect(self.add_to_cart_buttons.first).to_be_visible(timeout=timeout)
            return True
        except AssertionError:
            return False

    def add_first_option_to_cart(self) -> ThingsToDoPage:
        """Add the first room rate to the cart; lands on the Things To Do page.

        Example: cart = rates_page.add_first_option_to_cart().open_cart()
        """
        expect(self.add_to_cart_buttons.first).to_be_visible(timeout=30000)
        self.add_to_cart_buttons.first.click()
        return ThingsToDoPage(self.page).wait_until_loaded()
