import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from wait_job_finish import query_jobs


def test_query_jobs_rejects_zero_timeout():
    try:
        query_jobs("job-1", "scheduler.example", 3000, 0, 10)
    except ValueError as exc:
        assert "timeout" in str(exc)
    else:
        raise AssertionError("query_jobs should reject a zero timeout")


if __name__ == "__main__":
    test_query_jobs_rejects_zero_timeout()
