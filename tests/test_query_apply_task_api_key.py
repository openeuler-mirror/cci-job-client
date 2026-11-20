import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from lib.parse_tbox_spec import query_apply_task


def test_query_apply_task_rejects_empty_api_key():
    try:
        query_apply_task(1001, "")
    except ValueError as exc:
        assert "api_key" in str(exc)
    else:
        raise AssertionError("query_apply_task should reject an empty api_key")


if __name__ == "__main__":
    test_query_apply_task_rejects_empty_api_key()
