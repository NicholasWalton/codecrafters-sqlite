from app import _read_integer
from app.varint import varint_at


class TableLeafCell:
    def __init__(self, page, pointer, usable_size):
        payload_size, self.payload_size_length = varint_at(page, pointer)
        assert payload_size <= usable_size - 35  # let U be the usable size of a database page, the total page size less the reserved space at the end of each page. Let X be U-35. If the payload size P is less than or equal to X then the entire payload is stored on the b-tree leaf page
        self.slice = page[pointer:pointer + payload_size]
        rowid, rowid_length = varint_at(self.slice, self.payload_size_length)
        record = self.slice[self.payload_size_length + rowid_length:]
        header_size, header_size_length = varint_at(record, 0)
        column_types = []
        current_location = header_size_length
        while current_location < header_size:
            serial_type, length = varint_at(record, current_location)
            current_location += length
            column_types.append(serial_type)

        print(column_types)
        self.columns = []
        for serial_type_code in column_types:
            if serial_type_code in [1, 2, 3, 4, 6, 8]:
                self.columns.append(_read_integer(record, current_location, serial_type_code))
                current_location += serial_type_code
            elif serial_type_code >= 13 and serial_type_code % 2 == 1:
                string_length = (serial_type_code - 13) // 2
                entry = record[current_location:current_location + string_length]
                self.columns.append(entry.decode())
                current_location += string_length
            else:
                raise Exception(f"Unknown serial type code {serial_type_code}")