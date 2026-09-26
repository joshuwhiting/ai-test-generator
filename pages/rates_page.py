import re

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.things_to_do_page import ThingsToDoPage


class RatesPage(BasePage):
    """A hotel's accommodations page listing rooms and rates for the chosen dates."""

    def __init__(self, page):
        super().__init__(page)
        self.add_to_cart_buttons = page.get_by_role("button", name="Add to Cart")

    def wait_until_loaded(self) -> "RatesPage":
        expect(self.page).to_have_url(re.compile(r"/accommodations/"), timeout=30000)
        expect(self.add_to_cart_buttons.first).to_be_visible(timeout=30000)
        return self

    def add_first_option_to_cart(self) -> ThingsToDoPage:
        self.add_to_cart_buttons.first.click()
        return ThingsToDoPage(self.page).wait_until_loaded()
