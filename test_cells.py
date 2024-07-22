import pytest

from app import cells


@pytest.mark.parametrize("record,serial_type_code,expected_value,expected_content_size", (
        pytest.param([0x7f], 1, 127, 1, id="positive_value"),
        pytest.param([0xff], 1, -1, 1, id="negative_value"),
))
def test_decode_integer(record, serial_type_code, expected_value, expected_content_size):
    assert cells._decode(record, 0, serial_type_code) == (expected_value, expected_content_size)


@pytest.mark.parametrize("serial_type_code,expected_value", (
        pytest.param(8, 0, id="literal_zero"),
        pytest.param(9, 1, id="literal_one"),
        pytest.param(0, None, id="literal_null")
))
def test_decode_literal(serial_type_code, expected_value):
    assert cells._decode([], 0, serial_type_code) == (expected_value, 0)
