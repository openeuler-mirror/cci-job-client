import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'lib'))

from parse_tbox_spec import parse_params


def test_parse_params_skips_empty_keys():
    assert parse_params("=bad,arch=x86_64, memory=8G") == {
        "arch": "x86_64",
        "memory": "8G",
    }


if __name__ == "__main__":
    test_parse_params_skips_empty_keys()
    print("parse_tbox_spec parse_params tests passed")
