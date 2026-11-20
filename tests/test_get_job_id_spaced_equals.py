import os
import sys
import logging


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

logging.getLogger().addHandler(logging.NullHandler())

from submit_job import get_job_id


def test_get_job_id_accepts_spaces_around_equals():
    output = "submit done, got job id = job-12345, queued"
    assert get_job_id(output) == "job-12345"


if __name__ == "__main__":
    test_get_job_id_accepts_spaces_around_equals()
