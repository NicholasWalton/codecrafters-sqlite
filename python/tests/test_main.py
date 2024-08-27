import doctest

import codecrafters_sqlite


def test_docstring():
    assert doctest.testmod(m=codecrafters_sqlite).failed == 0
