from datetime import date, timedelta

from playwright.sync_api import Page

from pages.find_hotel_page import FindHotelPage


def test_book_miami_two_nights_four_weeks_out(page: Page, start_url: str) -> None:
    four_weeks_out = date.today() + timedelta(weeks=4)

    property_page = FindHotelPage(page).open(start_url).select_property("North America", "Miami")
    # If there are no rooms 4 weeks out, try the following weeks
    rates_page = property_page.booking_form.find_available_rates(four_weeks_out, nights=2, max_weeks=4)
    things_to_do = rates_page.add_first_option_to_cart()
    cart = things_to_do.open_cart()

    cart.expect_stay("Four Seasons Hotel Miami", rates_page.stay, rooms=1)
