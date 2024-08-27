import pytest

from codecrafters_sqlite import cells
from codecrafters_sqlite.cells import TableLeafCell, DecodeError


@pytest.mark.parametrize(
    "record,serial_type_code,expected_value,expected_content_size",
    (
        pytest.param([0x7F], 1, 127, 1, id="positive_value"),
        pytest.param([0xFF], 1, -1, 1, id="negative_value"),
    ),
)
def test_decode_integer(
    record, serial_type_code, expected_value, expected_content_size
):
    assert cells.decode(record, 0, serial_type_code) == (
        expected_value,
        expected_content_size,
    )


@pytest.mark.parametrize(
    "serial_type_code,expected_value",
    (
        pytest.param(8, 0, id="literal_zero"),
        pytest.param(9, 1, id="literal_one"),
        pytest.param(0, None, id="literal_null"),
    ),
)
def test_decode_literal(serial_type_code, expected_value):
    assert cells.decode([], 0, serial_type_code) == (expected_value, 0)


def test_decode_bad_unicode():
    with pytest.raises(DecodeError) as exc_info:
        cells.decode(b"\xb1", 0, 15)
    assert exc_info
    e = exc_info.value
    assert e.content_size == 1
    assert e.message.startswith("failed to decode")
    assert e.message.find("xb1")
    assert e.message.endswith("invalid start byte")
    assert isinstance(e.__cause__, UnicodeDecodeError)


def test_bad_unicode_in_cell():
    row_id = 0x00
    header_size = 0x03  # includes self
    one_byte_string_serial_type = (1 * 2) + 13
    invalid_unicode = 0xB1
    int8_serial_type = 1
    int8_value = 42
    page = bytearray(
        [
            0x00,
            row_id,
            header_size,
            one_byte_string_serial_type,
            int8_serial_type,
            invalid_unicode,
            int8_value,
        ]
    )
    page[0] = len(page)
    pointer = 0
    usable_size = 35 + len(page)
    cell = TableLeafCell(page, pointer, usable_size)
    message, actual_int8 = cell.columns
    assert cell.errors == 1
    assert actual_int8 == int8_value
    assert message.startswith("failed to decode")


def test_rowid():
    row_id = 0x01
    header_size = 0x02  # includes self
    literal_null = 0x00
    page = bytearray(
        [
            0x00,
            row_id,
            header_size,
            literal_null,
        ]
    )
    page[0] = len(page)
    pointer = 0
    usable_size = 35 + len(page)
    cell = TableLeafCell(page, pointer, usable_size)
    assert cell.columns == [
        row_id,
    ]
