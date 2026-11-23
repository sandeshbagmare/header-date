"""Tests for header_date."""

from datetime import datetime, timedelta, timezone

import pytest

from header_date import InvalidHTTPDate, format, now, parse, to_timestamp

IMF = "Sun, 06 Nov 1994 08:49:37 GMT"
RFC850 = "Sunday, 06-Nov-94 08:49:37 GMT"
ASCTIME = "Sun Nov  6 08:49:37 1994"


class TestParse:
    def test_imf_fixdate(self):
        moment = parse(IMF)
        assert moment == datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc)

    def test_rfc_850(self):
        assert parse(RFC850) == parse(IMF)

    def test_asctime(self):
        assert parse(ASCTIME) == parse(IMF)

    def test_the_result_is_aware_and_utc(self):
        moment = parse(IMF)
        assert moment.tzinfo is not None
        assert moment.utcoffset() == timedelta(0)

    def test_numeric_zone_offset(self):
        assert parse("Sun, 06 Nov 1994 08:49:37 +0000") == parse(IMF)

    def test_surrounding_whitespace_is_ignored(self):
        assert parse(f"  {IMF}  ") == parse(IMF)

    def test_case_insensitive_month_and_weekday(self):
        assert parse("sun, 06 nov 1994 08:49:37 GMT") == parse(IMF)

    def test_single_digit_day(self):
        assert parse("Sun, 6 Nov 1994 08:49:37 GMT").day == 6

    def test_four_digit_year_in_rfc_850(self):
        assert parse("Sunday, 06-Nov-1994 08:49:37 GMT").year == 1994

    def test_two_digit_year_after_70_is_the_1900s(self):
        assert parse("Sunday, 06-Nov-94 08:49:37 GMT").year == 1994

    def test_two_digit_year_before_70_is_the_2000s(self):
        assert parse("Wednesday, 01-Jan-25 00:00:00 GMT").year == 2025

    def test_leap_day(self):
        assert parse("Thu, 29 Feb 2024 00:00:00 GMT").day == 29

    def test_a_wrong_weekday_is_rejected_by_default(self):
        with pytest.raises(InvalidHTTPDate, match="weekday says Mon but 1994-11-06 is a Sun"):
            parse("Mon, 06 Nov 1994 08:49:37 GMT")

    def test_a_wrong_weekday_can_be_accepted(self):
        assert parse("Mon, 06 Nov 1994 08:49:37 GMT", strict=False) == parse(IMF)

    def test_an_unknown_month(self):
        with pytest.raises(InvalidHTTPDate, match="unknown month"):
            parse("Sun, 06 Foo 1994 08:49:37 GMT")

    def test_an_unknown_weekday(self):
        with pytest.raises(InvalidHTTPDate, match="unknown weekday"):
            parse("Xyz, 06 Nov 1994 08:49:37 GMT")

    def test_a_date_that_does_not_exist(self):
        with pytest.raises(InvalidHTTPDate, match="not a real date"):
            parse("Sat, 31 Feb 1994 08:49:37 GMT")

    def test_an_impossible_time(self):
        with pytest.raises(InvalidHTTPDate, match="not a real date"):
            parse("Sun, 06 Nov 1994 25:00:00 GMT", strict=False)

    def test_garbage(self):
        with pytest.raises(InvalidHTTPDate, match="not an HTTP date"):
            parse("last tuesday")

    def test_an_empty_value(self):
        with pytest.raises(InvalidHTTPDate, match="empty date"):
            parse("   ")

    def test_none_like_input(self):
        with pytest.raises(InvalidHTTPDate):
            parse(None)  # type: ignore[arg-type]


class TestFormat:
    def test_canonical_form(self):
        assert format(datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc)) == IMF

    def test_a_naive_datetime_is_taken_as_utc(self):
        assert format(datetime(1994, 11, 6, 8, 49, 37)) == IMF

    def test_another_zone_is_converted(self):
        moment = datetime(1994, 11, 6, 9, 49, 37, tzinfo=timezone(timedelta(hours=1)))
        assert format(moment) == IMF

    def test_padding_of_single_digit_parts(self):
        moment = datetime(2024, 1, 5, 4, 3, 2, tzinfo=timezone.utc)
        assert format(moment) == "Fri, 05 Jan 2024 04:03:02 GMT"

    def test_round_trip(self):
        for moment in [
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc),
            datetime(2024, 2, 29, 23, 59, 59, tzinfo=timezone.utc),
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        ]:
            assert parse(format(moment)) == moment


class TestNow:
    def test_now_is_a_parseable_http_date(self):
        moment = parse(now())
        assert abs((datetime.now(timezone.utc) - moment).total_seconds()) < 5

    def test_now_is_in_canonical_form(self):
        assert now().endswith("GMT")
        assert len(now()) == 29


class TestToTimestamp:
    def test_epoch(self):
        assert to_timestamp("Thu, 01 Jan 1970 00:00:00 GMT") == 0.0

    def test_a_later_date(self):
        assert to_timestamp(IMF) == 784111777.0
