import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lib'))

from parse_tbox_spec import get_hw_testboxes


def test_get_hw_testboxes_requires_api_key():
    try:
        get_hw_testboxes(api_key=None)
    except ValueError as exc:
        assert "api_key is required" in str(exc)
    else:
        raise AssertionError("get_hw_testboxes should require api_key")


if __name__ == "__main__":
    test_get_hw_testboxes_requires_api_key()
    print("hw api key tests passed")
