import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from lib.parse_tbox_spec import cancel_apply_task


def test_cancel_apply_task_rejects_empty_api_key():
    try:
        cancel_apply_task(1001, "")
    except ValueError as exc:
        assert "api_key" in str(exc)
    else:
        raise AssertionError("cancel_apply_task should reject an empty api_key")


if __name__ == "__main__":
    test_cancel_apply_task_rejects_empty_api_key()
