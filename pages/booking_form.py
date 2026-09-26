import re
from datetime import date

from playwright.sync_api import Page, expect

from pages.rates_page import RatesPage


def _calendar_label(day: date) -> str:
    # Matches the end of labels like "Available check-in date Saturday, October 24, 2026"
    return f"{day:%B} {day.day}, {day.year}"


class BookingForm:
    """The "Check Rates and Availability" form shown on property and rates pages."""

    def __init__(self, page: Page):
        self.page = page
        self.form = page.get_by_role("form", name="Check Rates and Availability")
        self.dates_button = self.form.get_by_role("button", name=re.compile(r"^Selected Dates"))
        self.calendar = self.form.get_by_role("dialog")
        self.next_month_button = self.calendar.get_by_role("button", name="Next month")
        self.apply_button = self.calendar.get_by_role("button", name="Apply")
        # exact: "Hide the Check Rates and Availability form" also contains "Check Rates"
        self.check_rates_button = self.form.get_by_role("button", name="Check Rates", exact=True)

    def select_dates(self, check_in: date, check_out: date) -> "BookingForm":
        self.dates_button.click()
        self._day_button("check-in", check_in).click()
        self._day_button("check-out", check_out).click()
        self.apply_button.click()
        expect(self.dates_button).to_have_accessible_name(re.compile(
            rf"{check_in:%B} {check_in.day} {check_in.year} to {check_out:%B} {check_out.day} {check_out.year}"
        ))
        return self

    def check_rates(self) -> RatesPage:
        self.check_rates_button.click()
        return RatesPage(self.page).wait_until_loaded()

    def _day_button(self, kind: str, day: date):
        """The calendar button for a check-in/check-out day, paging forward to its month if needed.

        Label prefixes vary ("Available check-out date", "Available for checkout", "Restricted.") and don't
        reliably say whether a day can be picked, so only the date is matched; select_dates() then checks
        that the form accepted the dates.
        """
        button = self.calendar.get_by_role("button", name=re.compile(rf"{re.escape(_calendar_label(day))}$"))
        for _ in range(12):
            if button.count() > 0:
                break
            self.next_month_button.click()

        expect(button, f"{day:%B} {day.day}, {day.year} can't be selected as a {kind} date").to_be_enabled()
        return button
