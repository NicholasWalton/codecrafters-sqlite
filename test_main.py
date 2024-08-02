import doctest

from app import main


def test_docstring():
    assert doctest.testmod(m=main).failed == 0
