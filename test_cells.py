from app import cells


def test_positive_value():
    assert cells._decode([0x7f], 0, 1) == (127, 1)


def test_negative_value():
    assert cells._decode([0xff], 0, 1) == (-1, 1)


def test_literal_zero():
    assert cells._decode([], 0, 8) == (0, 0)


def test_literal_one():
    assert cells._decode([], 0, 9) == (1, 0)


def test_null():
    assert cells._decode([], 0, 0) == (None, 0)
