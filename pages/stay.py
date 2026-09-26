from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Stay:
    """Check-in and check-out dates for a booking."""

    check_in: date
    check_out: date

    @classmethod
    def starting(cls, check_in: date, nights: int) -> "Stay":
        return cls(check_in, check_in + timedelta(days=nights))

    def one_week_later(self) -> "Stay":
        return Stay(self.check_in + timedelta(weeks=1), self.check_out + timedelta(weeks=1))
