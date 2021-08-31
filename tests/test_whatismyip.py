from __future__ import division, print_function
import pytest
import whatismyip


def test_basic():
    assert whatismyip.whatismyip(sources=('https://inventwithpython.com/whatismyip/',)) == '99.99.99.99'


if __name__ == "__main__":
    pytest.main()
