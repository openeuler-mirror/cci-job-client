import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from lib.parse_tbox_spec import apply_machines


def test_apply_machines_rejects_empty_ip_list():
    try:
        apply_machines([], 60, "api-key")
    except ValueError as exc:
        assert "ip_list" in str(exc)
    else:
        raise AssertionError("apply_machines should reject an empty ip_list")


if __name__ == "__main__":
    test_apply_machines_rejects_empty_ip_list()
