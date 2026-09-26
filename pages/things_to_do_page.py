from playwright.sync_api import expect

from pages.base_page import BasePage


class ThingsToDoPage(BasePage):
    """The "Things To Do" page shown after a room is added to the cart."""

    def __init__(self, page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Things To Do", level=1)

    def wait_until_loaded(self) -> "ThingsToDoPage":
        expect(self.heading).to_be_visible(timeout=30000)
        return self
