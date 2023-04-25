import pytest


def test_duration_in_seconds():
    from utilities import duration_in_seconds
    from datetime import datetime

    a = datetime(year=2023, month=1, day=1, hour=23, minute=30, second=0)
    b = datetime(year=2023, month=1, day=2, hour=0, minute=0, second=0)

    assert duration_in_seconds(a=a, b=b) == 1800 or 1800.0
