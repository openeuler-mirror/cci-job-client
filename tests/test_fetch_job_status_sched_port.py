import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from wait_job_finish import fetch_job_status


def test_fetch_job_status_rejects_zero_sched_port():
    try:
        fetch_job_status("job-1", "scheduler.example", 0)
    except ValueError as exc:
        assert "sched_port" in str(exc)
    else:
        raise AssertionError("fetch_job_status should reject a zero sched_port")


if __name__ == "__main__":
    test_fetch_job_status_rejects_zero_sched_port()
