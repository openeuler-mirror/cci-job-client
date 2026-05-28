import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from lib.parse_tbox_spec import return_machines


def test_return_machines_rejects_empty_api_key():
    try:
        return_machines(["192.0.2.10"], [1001], "")
    except ValueError as exc:
        assert "api_key" in str(exc)
    else:
        raise AssertionError("return_machines should reject an empty api_key")


if __name__ == "__main__":
    test_return_machines_rejects_empty_api_key()
