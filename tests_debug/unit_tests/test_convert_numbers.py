import pytest
from functions.data import time_to_decimal_hours


def test_time_to_decimal_hours_h_m_s():
    assert time_to_decimal_hours('1h 30m 15s') == 1.5 + 15/3600
    assert time_to_decimal_hours('1h 30m') == 1.5
    assert time_to_decimal_hours('45m') == 0.75


def test_colon_format():
    assert time_to_decimal_hours('00:30:00') == 0.5
    assert time_to_decimal_hours('1:30:00') == 1.5
    assert time_to_decimal_hours('12:05') == 12/60 + 5/3600


def test_numeric_input_seconds():
    # Numeric inputs are seconds in new format
    assert time_to_decimal_hours(3600) == 1.0
    assert time_to_decimal_hours(5400) == 1.5
    assert time_to_decimal_hours(6724) == 1.87  # 6724 / 3600 = 1.8677 -> 1.87
    assert time_to_decimal_hours(None) is None


def test_decimal_hours_string():
    assert time_to_decimal_hours('1.5h') == 1.5
    assert time_to_decimal_hours('2') == 2.0
