# header-date

Parse and format HTTP dates — and refuse the ones whose weekday is a lie.

[![PyPI](https://img.shields.io/pypi/v/header-date.svg)](https://pypi.org/project/header-date/)
[![Python](https://img.shields.io/pypi/pyversions/header-date.svg)](https://pypi.org/project/header-date/)
[![tests](https://github.com/sandeshbagmare/header-date/actions/workflows/ci.yml/badge.svg)](https://github.com/sandeshbagmare/header-date/actions/workflows/ci.yml)
[![license](https://img.shields.io/pypi/l/header-date.svg)](https://github.com/sandeshbagmare/header-date/blob/main/LICENSE)

```python
>>> from header_date import format, parse
>>> parse("Sun, 06 Nov 1994 08:49:37 GMT").isoformat()
'1994-11-06T08:49:37+00:00'
>>> format(parse("Sunday, 06-Nov-94 08:49:37 GMT"))
'Sun, 06 Nov 1994 08:49:37 GMT'
>>> parse("Mon, 06 Nov 1994 08:49:37 GMT")
Traceback (most recent call last):
  ...
header_date.InvalidHTTPDate: weekday says Mon but 1994-11-06 is a Sun
```

`email.utils.parsedate_to_datetime` parses all three historical formats and quietly
ignores a weekday that contradicts the date. That is the one field a broken clock or a
hand-edited header gets wrong, and it is the field a cache validator depends on. This
library reads the same formats and checks it.

## Install

```console
pip install header-date
```

## Use

```python
from header_date import InvalidHTTPDate, format, now, parse, to_timestamp

parse("Sun, 06 Nov 1994 08:49:37 GMT")            # aware datetime in UTC
parse("Mon, 06 Nov 1994 08:49:37 GMT", strict=False)  # accept the wrong weekday
format(moment)                                     # 'Sun, 06 Nov 1994 08:49:37 GMT'
now()                                              # the current time, canonical form
to_timestamp("Thu, 01 Jan 1970 00:00:00 GMT")       # 0.0
```

## What is accepted

| form | example |
| ---- | ------- |
| IMF-fixdate (RFC 9110) | `Sun, 06 Nov 1994 08:49:37 GMT` |
| RFC 850 (obsolete) | `Sunday, 06-Nov-94 08:49:37 GMT` |
| asctime (obsolete) | `Sun Nov  6 08:49:37 1994` |

- zones `GMT`, `UTC` and numeric `+0000` are accepted; anything else is rejected
- month and weekday names are matched case-insensitively, and full weekday names work
- a two-digit year maps to the most recent past year with those digits (`94` → 1994,
  `25` → 2025), as RFC 9110 asks
- impossible dates (`31 Feb`, `25:00:00`) are rejected, not rolled over
- `format` always writes the canonical IMF-fixdate, converting other zones to UTC

## Limits

- Only seconds resolution: HTTP dates have no fractional seconds.
- Leap seconds (`:60`) are rejected.
- `format` does not support years before 1000 or after 9999.

## Development

```console
python -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/pytest
```

## License

MIT.
