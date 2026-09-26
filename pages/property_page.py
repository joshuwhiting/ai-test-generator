from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.booking_form import BookingForm


class PropertyPage(BasePage):
    """A hotel's home page, e.g. /miami/, with the Check Rates booking form."""

    def __init__(self, page):
        super().__init__(page)
        self.booking_form = BookingForm(page)

    def wait_until_loaded(self) -> "PropertyPage":
        expect(self.booking_form.form).to_be_visible(timeout=15000)
        return self
