"""Parse and format HTTP dates, and check that the weekday is real.

``email.utils.parsedate_to_datetime`` accepts almost anything and ignores a weekday
that contradicts the date. HTTP requires the day name to be right — RFC 9110 says a
recipient *may* reject a date whose weekday disagrees — and a wrong weekday is exactly
what a hand-written header or a broken clock produces.

    >>> from header_date import format, parse
    >>> parse("Sun, 06 Nov 1994 08:49:37 GMT").isoformat()
    '1994-11-06T08:49:37+00:00'
    >>> format(parse("Sunday, 06-Nov-94 08:49:37 GMT"))
    'Sun, 06 Nov 1994 08:49:37 GMT'

All three historical formats are read (IMF-fixdate, RFC 850, asctime); only the
canonical one is written. Standard library only, Python 3.9+.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

__all__ = ["InvalidHTTPDate", "format", "now", "parse", "to_timestamp"]

__version__ = "0.1.0"

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_WEEKDAYS = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_ZONE = r"(?:GMT|UTC|[+-]\d{4})"
_IMF = re.compile(
    r"^(?P<weekday>[A-Za-z]{3}),\s+(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]{3})\s+"
    rf"(?P<year>\d{{4}})\s+(?P<hour>\d{{2}}):(?P<minute>\d{{2}}):(?P<second>\d{{2}})\s+{_ZONE}$"
)
_RFC850 = re.compile(
    r"^(?P<weekday>[A-Za-z]+),\s+(?P<day>\d{1,2})-(?P<month>[A-Za-z]{3})-"
    rf"(?P<year>\d{{2,4}})\s+(?P<hour>\d{{2}}):(?P<minute>\d{{2}}):(?P<second>\d{{2}})\s+{_ZONE}$"
)
_ASCTIME = re.compile(
    r"^(?P<weekday>[A-Za-z]{3})\s+(?P<month>[A-Za-z]{3})\s+(?P<day>\d{1,2}|\s\d)\s+"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})\s+(?P<year>\d{4})$"
)


class InvalidHTTPDate(ValueError):
    """A value that is not a valid HTTP date."""


def _two_digit_year(year: int) -> int:
    """RFC 9110: a two-digit year is the most recent past year with those digits."""
    return year + (1900 if year >= 70 else 2000)


def parse(value: str, *, strict: bool = True) -> datetime:
    """Parse an HTTP date into an aware UTC :class:`datetime`.

    ``strict`` (the default) rejects a date whose weekday name does not match the date
    it carries; pass ``strict=False`` to accept it and use the date.
    """
    text = (value or "").strip()
    if not text:
        raise InvalidHTTPDate("empty date")
    match = _IMF.match(text) or _RFC850.match(text) or _ASCTIME.match(text)
    if match is None:
        raise InvalidHTTPDate(f"not an HTTP date: {value!r}")

    fields = match.groupdict()
    month_name = fields["month"].lower()
    if month_name not in _MONTHS:
        raise InvalidHTTPDate(f"unknown month: {fields['month']!r}")
    weekday_name = fields["weekday"].lower()
    if weekday_name not in _WEEKDAYS:
        raise InvalidHTTPDate(f"unknown weekday: {fields['weekday']!r}")

    year = int(fields["year"])
    if len(fields["year"]) == 2:
        year = _two_digit_year(year)
    try:
        moment = datetime(
            year,
            _MONTHS[month_name],
            int(fields["day"]),
            int(fields["hour"]),
            int(fields["minute"]),
            int(fields["second"]),
            tzinfo=timezone.utc,
        )
    except ValueError as error:
        raise InvalidHTTPDate(f"not a real date: {value!r} ({error})") from None

    if strict and moment.weekday() != _WEEKDAYS[weekday_name]:
        raise InvalidHTTPDate(
            f"weekday says {_WEEKDAY_NAMES[_WEEKDAYS[weekday_name]]} but "
            f"{moment.date().isoformat()} is a {_WEEKDAY_NAMES[moment.weekday()]}"
        )
    return moment


def format(moment: datetime) -> str:
    """Format a :class:`datetime` as an IMF-fixdate, in UTC."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    else:
        moment = moment.astimezone(timezone.utc)
    return (
        f"{_WEEKDAY_NAMES[moment.weekday()]}, {moment.day:02d} "
        f"{_MONTH_NAMES[moment.month - 1]} {moment.year:04d} "
        f"{moment.hour:02d}:{moment.minute:02d}:{moment.second:02d} GMT"
    )


def now() -> str:
    """The current time as an HTTP date."""
    return format(datetime.now(timezone.utc))


def to_timestamp(value: str) -> float:
    """Parse an HTTP date into a Unix timestamp."""
    return parse(value).timestamp()
