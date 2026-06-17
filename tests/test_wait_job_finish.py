import os
import sys
from unittest import mock

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import wait_job_finish


def test_wait_job_status_exits_when_final_status_request_fails():
    with mock.patch.object(wait_job_finish, "query_jobs", return_value=("finish", "suite")):
        with mock.patch.object(
            wait_job_finish,
            "fetch_job_status",
            side_effect=requests.exceptions.ConnectionError("refused"),
        ):
            with pytest.raises(SystemExit) as exc:
                wait_job_finish.wait_job_status(
                    "job-1",
                    "127.0.0.1",
                    8080,
                    poll_interval=0,
                    timeout=1,
                )

    assert exc.value.code == 1
