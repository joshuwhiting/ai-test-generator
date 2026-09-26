import re
from datetime import date

from playwright.sync_api import Page, expect

from pages.rates_page import RatesPage
from pages.stay import Stay


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
        self._stay: Stay | None = None

    def select_dates(self, check_in: date, check_out: date) -> "BookingForm":
        """Pick exact dates in the calendar (fails if they can't be picked). Follow with check_rates().

        Example: rates_page = property_page.booking_form.select_dates(check_in, check_out).check_rates()
        """
        self.dates_button.click()
        self._day_button("check-in", check_in).click()
        self._day_button("check-out", check_out).click()
        self.apply_button.click()
        expect(self.dates_button).to_have_accessible_name(re.compile(
            rf"{check_in:%B} {check_in.day} {check_in.year} to {check_out:%B} {check_out.day} {check_out.year}"
        ))
        self._stay = Stay(check_in, check_out)
        return self

    def check_rates(self) -> RatesPage:
        if self._stay is None:
            raise AssertionError("Call select_dates() before check_rates()")
        self.check_rates_button.click()
        return RatesPage(self.page, self._stay).wait_until_loaded()

    def find_available_rates(self, check_in: date, nights: int, max_weeks: int = 4) -> RatesPage:
        """Check rates from check_in for the given nights; if nothing is available, try again a week later.

        Tries up to max_weeks different weeks. The returned RatesPage's .stay has the dates that had rooms.
        Use this instead of select_dates() + check_rates() when the flow should retry on no availability.
        Example: rates_page = property_page.booking_form.find_available_rates(date.today() + timedelta(weeks=4), nights=2)
        """
        stay = Stay.starting(check_in, nights)
        for _ in range(max_weeks):
            try:
                self.select_dates(stay.check_in, stay.check_out)
            except AssertionError:
                print(f"No availability from {stay.check_in} (dates can't be selected); trying a week later")
                self.page.reload()  # reset the half-filled calendar
                stay = stay.one_week_later()
                continue

            rates_page = self.check_rates()
            if rates_page.has_rooms():
                return rates_page
            print(f"No rooms from {stay.check_in} for {nights} nights; trying a week later")
            stay = stay.one_week_later()  # the rates page has the same booking form, so search again from here

        raise AssertionError(f"No availability for {nights} nights in {max_weeks} weeks starting {check_in}")

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
