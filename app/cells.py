import logging
from pprint import pformat

from app import _buffer, _read_integer
from app.varint import varint

logger = logging.getLogger(__name__)


class DecodeError(Exception):
    def __init__(self, message, content_size):
        self.message = message
        self.content_size = content_size


class VarintReader:
    def __init__(self, buffer):
        self.buffer = buffer

    def __next__(self):
        value, length = varint(self.buffer)
        self.buffer = self.buffer[length:]
        return value, length

    def read(self, buffer_size):
        size = 0
        while size < buffer_size:
            value, length = next(self)
            size += length
            yield value


class TableLeafCell:
    def __init__(self, page, pointer, usable_size):
        self.errors = 0
        record_varints = VarintReader(page[pointer:])
        payload_size, self.payload_size_length = next(record_varints)
        assert (
            payload_size <= usable_size - 35
        )  # let U be the usable size of a database page, the total page size less the reserved space at the end of each page. Let X be U-35. If the payload size P is less than or equal to X then the entire payload is stored on the b-tree leaf page

        rowid, rowid_length = next(record_varints)
        self.id_message = f"rowid {rowid}: {payload_size} bytes at {pointer}"
        logger.debug(self.id_message)
        self._cell = _buffer(
            page, pointer, payload_size + self.payload_size_length + rowid_length
        )
        self._record = self._cell[self.payload_size_length + rowid_length :]
        header_size, header_size_length = next(record_varints)

        column_types = list(record_varints.read(header_size - header_size_length))
        logger.debug(f"Rowid {rowid} serial type codes: {column_types}")

        body = record_varints.buffer
        self.columns = list(self._read_columns(column_types, body))

        if self.columns[0] is None:
            self.columns[0] = rowid

    def _read_columns(self, column_types, body):
        current_location = 0
        for serial_type_code in column_types:
            try:
                content, content_size = decode(body, current_location, serial_type_code)
            except DecodeError as e:
                content = e.message
                content_size = e.content_size
                self.errors += 1
            current_location += content_size
            yield content
        if self.errors != 0:
            self._log_errors(current_location)

    def _log_errors(self, current_location):
        logger.error(f"{self.errors} cell errors for {self.id_message}")
        logger.error(f"Cell: {pformat(self._cell, indent=4)}")
        logger.error(f"Record: {pformat(self._record, indent=4)}")
        logger.error(
            f"Remainder of columns: {pformat(self._record[current_location:], indent=4)}"
        )


def decode(record, current_location, serial_type_code):
    match serial_type_code:
        case 0:
            return None, 0
        case 8:
            return 0, 0
        case 9:
            return 1, 0
        case 1 | 2 | 3 | 4 | 6:
            content = _read_integer(
                record, current_location, serial_type_code, signed=True
            )
            return content, serial_type_code
        case _:
            if serial_type_code >= 13 and serial_type_code % 2 == 1:
                string_length = (serial_type_code - 13) // 2
                entry = record[current_location : current_location + string_length]
                logger.debug(f"decoded [{entry}] with length {string_length}")
                try:
                    decoded = entry.decode()
                except UnicodeDecodeError as e:
                    message = f"failed to decode [{entry}] at {current_location}: {e}"
                    logger.error(message)
                    raise DecodeError(message, string_length) from e
                return decoded, string_length
    raise Exception(f"Unknown serial type code {serial_type_code}")
