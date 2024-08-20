import doctest

import app


def test_docstring():
    assert doctest.testmod(m=app).failed == 0
