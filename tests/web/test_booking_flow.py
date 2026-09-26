from datetime import date, timedelta

from playwright.sync_api import Page

from pages.find_hotel_page import FindHotelPage


def test_book_miami_two_nights_four_weeks_out(page: Page, start_url: str) -> None:
    check_in = date.today() + timedelta(weeks=4)
    check_out = check_in + timedelta(days=2)

    property_page = FindHotelPage(page).open(start_url).select_property("North America", "Miami")
    rates_page = property_page.booking_form.select_dates(check_in, check_out).check_rates()
    things_to_do = rates_page.add_first_option_to_cart()
    cart = things_to_do.open_cart()

    cart.expect_stay("Four Seasons Hotel Miami", check_in, check_out, rooms=1)
