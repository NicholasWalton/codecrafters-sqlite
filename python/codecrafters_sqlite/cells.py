import logging
from pprint import pformat

from codecrafters_sqlite import _buffer, _read_integer
from codecrafters_sqlite.varint import decode_varint

logger = logging.getLogger(__name__)


class DecodeError(Exception):
    def __init__(self, message, content_size):
        self.message = message
        self.content_size = content_size


class VarintReader:
    def __init__(self, buffer):
        self.buffer = buffer

    def __next__(self):
        value, length = decode_varint(self.buffer)
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
        self._pointer = pointer
        self.page_pointer_ = page[self._pointer :]
        self.usable_size = usable_size

    def _read_body(self):
        record_varints = VarintReader(self.page_pointer_)
        payload_size, payload_size_length = next(record_varints)
        assert (
            payload_size <= self.usable_size - 35
        )  # let U be the usable size of a database page, the total page size less the reserved space at the end of each page. Let X be U-35. If the payload size P is less than or equal to X then the entire payload is stored on the b-tree leaf page

        self.rowid, rowid_length = next(record_varints)
        self.id_message = f"rowid {self.rowid}: {payload_size} bytes at {self._pointer}"
        logger.debug(self.id_message)
        self._cell = _buffer(
            self.page_pointer_,
            0,
            payload_size + payload_size_length + rowid_length,
        )
        self._record = self._cell[payload_size_length + rowid_length :]
        header_size, header_size_length = next(record_varints)

        serial_type_codes = list(record_varints.read(header_size - header_size_length))
        logger.debug(f"Rowid {self.rowid} serial type codes: {serial_type_codes}")

        return record_varints.buffer, serial_type_codes

    @property
    def columns(self):
        columns = list(self._read_columns())
        if columns[0] is None:
            columns[0] = self.rowid
        return columns

    def _read_columns(self):
        current_location = 0
        body, serial_type_codes = self._read_body()
        for serial_type_code in serial_type_codes:
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

    @property
    def body(self):
        body, _ = self._read_body()
        return body

    @property
    def serial_type_codes(self):
        _, result = self._read_body()
        return result

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
