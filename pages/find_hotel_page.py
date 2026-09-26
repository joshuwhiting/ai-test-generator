import re

from playwright.sync_api import Error as PlaywrightError, expect

from pages.base_page import BasePage
from pages.property_page import PropertyPage


class FindHotelPage(BasePage):
    """The "Find a Hotel or Resort" page: tabs of properties grouped into region accordions."""

    def open(self, url: str) -> "FindHotelPage":
        self.page.goto(url)
        return self

    def select_property(self, region: str, name: str) -> PropertyPage:
        """Open the region's accordion (if closed) and click the property.

        The page rebuilds its tabs after loading and again after the cookie banner is accepted,
        which can close the accordion or move the link mid-click, so each attempt starts over.
        """
        link = self._region_section(region).get_by_role("link", name=name, exact=True)
        for _ in range(3):
            self._wait_for_tabs_ready()
            self._ensure_region_open(region)
            try:
                expect(link).to_be_visible(timeout=3000)
                link.click(timeout=5000)
                return PropertyPage(self.page).wait_until_loaded()
            except (AssertionError, PlaywrightError):
                continue
        raise AssertionError(f'Could not select "{name}" in the "{region}" region')

    def _active_tab(self):
        # Every tab has its own copy of the region accordions; only the active one is visible once the page settles
        return self.page.get_by_role("tabpanel").filter(visible=True)

    def _wait_for_tabs_ready(self) -> None:
        expect(self._active_tab()).to_have_count(1, timeout=15000)

    def _region_button(self, region: str):
        return self._active_tab().get_by_role("button", name=re.compile(rf"^{re.escape(region)}\b"))

    def _region_section(self, region: str):
        return self._active_tab().get_by_role("region", name=re.compile(rf"^{re.escape(region)}\b"))

    def _ensure_region_open(self, region: str) -> None:
        # Only click when closed: clicking an open accordion closes it
        button = self._region_button(region)
        if button.get_attribute("aria-expanded") != "true":
            button.click()
