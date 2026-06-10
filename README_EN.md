# Job submission and Waiting

## Project Overview

This project provides three Python scripts to automate the submission and monitoring of Linux Kernel Performance (LKP) test jobs. Key features include:

- `submit_job.py`：Submits an LKP job to the scheduler and returns the job ID (`job_id`).
- `wait_job_finish.py`: Polls the job status until completion or timeout.
- `submit_wait_job.py`：Combines the functionality of the two scripts above to submit a job and wait for its completion in a single execution.

These scripts can be used independently or combined to build an end-to-end job submission and monitoring workflow.

## Environment Settings

### Operating System

- Linux distributions (openEuler, Debian/Ubuntu, or CentOS/RHEL recommended)
- Root or sudo privileges required to install system dependencies

### Software Dependencies

- Python 3.6+
- Git
- cpio
- Ruby and gem
- Ruby gems: rest-client, concurrent-ruby
- LKP client (cloned automatically by the scripts)

### Python Dependency Installation

Openeuler

```bash
pip install -r requirements.txt
```

Debian

```bash
apt install -y python3-requests python3-yaml
```

## Installation and Configuration

### 1. Clone the Repository

```bash
# Clone the repository (replace with your actual repository URL).
git clone https://github.com/your-org/Jenkins-jobs.git
cd Jenkins-jobs
```

### 2. Install System Dependencies

The project provides a setup.py script to automate dependency installation.

```bash
# Automatically detect the system and install dependencies in the root directory.
python3 setup.py

# If automatic detection fails, forcibly specify an OS.
python3 setup.py --force-debian    # Debian/Ubuntu
python3 setup.py --force-openeuler # openEuler/CentOS/RHEL 

# If Python dependencies have been installed, skip this step.
python3 setup.py --skip-python
```

### 3. Verify Installation

After installation, run the following commands to verify that the scripts are working correctly:

```bash
# View script help information.
python3 src/submit_job.py --help
python3 src/wait_job_finish.py --help
python3 src/submit_wait_job.py --help

# Check Python dependencies.
python3 -c "import requests; import json; print('Dependency check passed')"
```

### 4. Configure Scheduler Information

The default scheduler address is `172.168.178.181:3000`. You can override this by specifying it via command-line arguments.

## Instructions

### Submit Job (submit_job.py)

#### Basic Usage

```bash
python3 src/submit_job.py
```

Submit a job using default arguments and return `job_id`.

#### Common Usage Example

```bash
python3 src/submit_job.py \
  --os openeuler \
  --os_arch aarch64 \
  --os_version 24.03-LTS \
  --testbox vm-2p8g \
  --my_account your_account \
  --my_name your_name \
  --my_token your_token \
  --my_email your_email@example.com \
  --job_yaml host-info.yaml \
  --sched_host 192.168.1.100 \
  --sched_port 3000
```

#### Argument Description

| Argument | Default Value | Description                                                                                        |
|------|--------|--------------------------------------------------------------------------------------------|
| `--os` | `openeuler` | OS name                                                                                     |
| `--os_arch` | `aarch64` | OS architecture                                                                                     |
| `--os_version` | `24.03-LTS` | OS version                                                                                     |
| `--testbox` | `vm-2p8g` | Textbox type                                                                                      |
| `--my_account` | `my_account` | User account                                                                                       |
| `--my_name` | `my_name` | User name                                                                                       |
| `--my_token` | `my_token` | Authentication token                                                                                       |
| `--my_email` | `my_email@qq.com` | User email                                                                                       |
| `--job_yaml` | `host-info.yaml` | Path to the job YAML file                                                                               |
| `--sched_host` | `172.168.178.181` | Scheduler host address                                                                                    |
| `--sched_port` | `3000` | Scheduler port                                                                                      |
| `--extra` | None | Extra key-value pairs (`key=value`). Repeatable, supports space-separated multiple pairs (e.g., `--extra "kernel=linux-5.10 memory=8G cpu=4"`). |
| `--skip_prepare` | None | Skip LKP client setup/preparation (if it already exists).                                                                        |

#### Output Example

```sh
============================================================
Step 2: Prepare LKP client environment
============================================================
LKP_SRC path is /c/lkp-tests
============================================================
Step 3: Submit job host-info.yaml
============================================================
Executing command: /c/lkp-tests/sbin/submit host-info.yaml
Response after submission: got job id=123456, ...
Job submitted successfully, job id = 123456
123456
```

Note: The last line of the output (`123456`) represents `job_id`, which can be captured for subsequent monitoring.

### Wait for Job Completion (wait_job_finish.py)

#### Basic Usage

```bash
python3 src/wait_job_finish.py --job_id 123456
```

#### Common Usage Example

```bash
python3 src/wait_job_finish.py \
  --job_id 123456 \
  --sched_host 192.168.1.100 \
  --sched_port 3000 \
  --poll_interval 5 \
  --timeout 7200
```

#### Argument Description

| Argument | Default Value | Description |
|------|--------|------|
| `--job_id` | - | (Required) Job ID, obtained from  `submit_job.py` |
| `--sched_host` | `172.168.178.181` | Scheduler host address |
| `--sched_port` | `3000` | Scheduler port |
| `--poll_interval` | `10` | Polling interval (seconds) |
| `--timeout` | `86400` | Maximum wait time (seconds); default value is 24 hours |

#### Job Status Definitions

The script polls the job status until it reaches one of the following terminal states:

- `finish`：The job completed successfully.
- `abort_invalid`：The job was aborted due to an invalid configuration.
- `abort_provider`：The job was aborted due to provider issues.

#### Output Example

```sh
============================================================
步骤1: Polling job status.API: http://172.168.178.181:3000/scheduler/v1/jobs/123456?fields=job_stage
============================================================
Current Job:lmbench, Job ID：xxxxx，Job Status：running
Current Job:lmbench, Job ID：xxxxx，Job Status：running
Current Job:lmbench, Job ID：xxxxx，Job Status：finish
lmbench:xxxxx job terminated, Status:finish
Full Job Info：{...}
```

### Submit and Wait for Job (submit_wait_job.py)

#### Basic Usage

```bash
python3 src/submit_wait_job.py
```

Submit a job using default arguments and wait until completion.

#### Common Usage Example

```bash
python3 src/submit_wait_job.py \
  --os openeuler \
  --os_arch aarch64 \
  --os_version 24.03-LTS \
  --testbox vm-2p8g \
  --my_account your_account \
  --my_name your_name \
  --my_token your_token \
  --my_email your_email@example.com \
  --job_yaml host-info.yaml \
  --sched_host 192.168.1.100 \
  --sched_port 3000 \
  --poll_interval 10 \
  --timeout 86400
```

#### Argument Description

| Argument | Default Value | Description |
|------|--------|------|
| `--os` | `openeuler` | OS name |
| `--os_arch` | `aarch64` | OS architecture |
| `--os_version` | `24.03-LTS` | OS version |
| `--testbox` | `vm-2p8g` | Testbox type |
| `--my_account` | `my_account` | User account |
| `--my_name` | `my_name` | User name |
| `--my_token` | `my_token` | Authentication token |
| `--my_email` | `my_email@qq.com` | User email |
| `--job_yaml` | `host-info.yaml` | Path to the job YAML file |
| `--sched_host` | `172.168.178.181` | Scheduler host address |
| `--sched_port` | `3000` | Scheduler port |
| `--extra` | None | Extra key-value pairs (`key=value`). Repeatable, supports space-separated multiple pairs (e.g.,`--extra "kernel=linux-5.10 memory=8G cpu=4"`)  |
| `--skip_prepare` | None | Skip LKP client setup/preparation (if it already exists). |
| `--poll_interval` | `10` | Polling interval (seconds) |
| `--timeout` | `86400` | Maximum wait time (seconds); default value is 24 hours |

#### Output Example

```sh
============================================================
Step 1: Submit LKP Job
============================================================
...（Output from submit_job.py）...
Job submitted successfully，job_id = 123456
============================================================
步骤2: Waiting for job 123456 to complete
============================================================
...（Output from wait_job_finish.py）...
Final Job Status：finish
============================================================
Done: Job processed successfully
============================================================
```

#### Important Notes

- This script sequentially invokes `submit_job.py` and `wait_job_finish.py`. Ensure dependencies for both scripts are fully satisfied.
- If submission fails, the script exits immediately with an error and will not enter the waiting phase.
- If a timeout occurs during waiting, the script exits with a non-zero status code.

### Workflow Integration Examples

#### Example 1: Submit and Wait (Simple Pipeline)

```bash
# Submit job and capture the job_id
JOB_ID=$(python3 src/submit_job.py --my_account real_account --my_token real_token)

# Wait for the job to finish
python3 src/wait_job_finish.py --job_id $JOB_ID
```

#### Example 2: Submit and Wait (Complete Script)

```bash
#!/bin/bash

# Submit job
echo "Submitting job..."
JOB_ID=$(python3 src/submit_job.py \
  --os openeuler \
  --os_arch aarch64 \
  --testbox vm-4p16g \
  --my_account "test_user" \
  --my_token "xxxxxx" \
  --job_yaml "my-test.yaml")

echo "作业 ID: $JOB_ID"

# Wait for job completion
echo "Waiting for job to complete..."
python3 src/wait_job_finish.py \
  --job_id $JOB_ID \
  --poll_interval 5 \
  --timeout 3600

if [ $? -eq 0 ]; then
  echo "Job completed successfully"
else
  echo "Job execution or monitoring failed"
  exit 1
fi
```

#### Example 3: Batch Job Submission

```bash
#!/bin/bash

for i in {1..5}; do
  echo "Submitting job $i..."
  JOB_ID=$(python3 src/submit_job.py --job_yaml "job$i.yaml")
  echo "Job $i ID: $JOB_ID"
  # Wait jobs to complete or record IDs for subsequent operations
done
```

## Configuration File Management

The project uses a centralized configuration file at `src/lib/constant.py` to manage default arguments across all scripts. Modifying constants here updates default behavior globally without altering script logic.

### Configuration File Structure

```python
# CCI Repository root directory, defaults to /c
CCI_REPOS = "/c"

# LKP source code path, defaults to /c/lkp-tests
LKP_SRC_PATH = Path(CCI_REPOS) / "lkp-tests"

# Default job submission arguments
OS_NAME = "openeuler"
OS_ARCH = "aarch64"
OS_VERSION = "24.03-LTS"
TESTBOX = "vm-2p8g"
MY_ACCOUNT = "my_account"
MY_NAME = "my_name"
MY_TOKEN = "my_token"
MY_EMAIL = "my_email@qq.com"
JOB_YAML = "host-info.yaml"
SCHED_PORT = 3000
SCHED_HOST = "172.168.178.181"
```

### How to Use

1. **Value Modifications**：Directly edit and save the target constant values in `src/lib/constant.py`.
2. **Automatic Script**：Both `submit_job.py` and `submit_wait_job.py` automatically import these constants as fallback values for command-line options.
3. **Precedence Rule**：Command-line flags always override configuration file defaults. For example, explicitly passing `--os` takes precedence over `OS_NAME`.

### Configuration Example

To update the default scheduler host globally to `192.168.1.100`，modify `SCHED_HOST`：

```python
SCHED_HOST = "192.168.1.100"
```

Subsequent script executions will fall back to this new host if `--sched_host` is omitted.

### Important Notes

- Changes to the configuration file take effect on the next script run; no service restart is required.
- Ensure that constant data types match the expected types(e.g., `SCHED_PORT` must remain an integer).
- Use standard Linux forward slashes (/) for any file path values.

## Advanced Configuration

### Custom LKP Client Path

By default, the script clones the LKP client into `/c/lkp-tests`. To bring your own pre-existing LKP client, pass the `--skip_prepare` flag and ensure your `LKP_SRC` environment variable points to your custom path.

### Custom Job YAML Definition

LKP jobs are structured via YAML files. You can define customized workloads as follows:

```yaml
# my-test.yaml
suite: hackbench
testbox: vm-2p8g
os: openeuler
os_arch: aarch64
os_version: 24.03-LTS
```

Submit the custom file via:

```bash
python3 src/submit_job.py --job_yaml my-test.yaml
```

### Environment Variables

You can also leverage system environment variables to set default arguments:

```bash
export SCHED_HOST="192.168.1.100"
export SCHED_PORT="3000"
export MY_ACCOUNT="my_account"
export MY_TOKEN="my_token"

# Scripts will automatically evaluate these environment variables
python3 src/submit_job.py
```

## Troubleshooting

### Common Issues

#### 1. Submission Failed: LKP Client Not Found

**Error Message**: `Submission command not found: /c/lkp-tests/sbin/submit`

**Solution**:

- Verify write permissions for the `/c` directory.
- Alternatively, use `--skip_prepare` and manually export the `LKP_SRC` environment variable.
- Manually clone the LKP client：`git clone https://gitee.com/compass-ci/lkp-tests.git /c/lkp-tests`

#### 2. Authentication Failed

**Error Message**:`Request exception: authentication failed`

**Solution**:

- Verify the validity of the `--my_token` setting.
- Ensure the associated account holds proper job submission permissions.
- Contact the scheduler administrator to validate account status.

#### 3. Network Connectivity Issues

**Error Message**: `Request exception: Connection refused`
**Solution**:

- Check that the scheduler address and port are correct.
- Run `ping <sched_host>` to verify network reachability.
- Verify that the scheduler daemon process is actively running.

#### 4. Job Hangs Indefinitely

**Solution**:

- Set an upper bound using the `--timeout` argument.
- Inspect scheduler control logs to diagnose state progression issues.
- Manually terminate or abort the stalled job entry if necessary.

### Debugging Mode

To view debugging details, modify the script or add logs:

```python
# Add the following to submit_job.py for temperary modifications
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Script Workflows

### submit_job.py Execution Flow

1. Prepares the LKP client environment (clones the repository if missing).
2. Exports essential environment variables（e.g., OS, architecture, textbox）
3. Runs `lkp-tests/sbin/submit` to submit job YAML.
4. Parses the output to isolate the assigned `job_id`.
5. Returns `job_id`.

### wait_job_finish.py Execution Flow

1. Constructs the scheduler API endpoint:`http://<host>:<port>/scheduler/v1/jobs/<job_id>?fields=job_stage`
2. Polls the job state at regular intervals.
3. Evaluates if the state matches a terminal identifier (`finish`/`abort*`).
4. Logs the final status along with full payload details.

### submit_wait_job.py Execution Flow

1. Invokes `submit_job.py` to obtain the job ID.
2. Invokes `wait_job_finish.py` to wait a job to complete.
3. Unifies stderr/stdout aggregation and exposes a streamlined return path.

## Script Return Codes

All three scripts follow standardized return code conventions:

- **0**: Process completed successfully.
- **1**：Invalid arguments or malformed user input.
- **2**：Network connection failure or scheduler unreachable.
- **3**：Job submission failed (Authentication/Authorization error).
- **4**：Job waiting phase timed out.
- **5**：Missing core system dependencies (e.g., LKP client missing).
- **Other non-zero values**: Uncaught or unexpected runtime exceptions.

You can inspect these programmatically within shell workflows via `$?`:

```bash
python3 src/submit_job.py
if [ $? -eq 0 ]; then
    echo "Job submitted successfully"
else
    echo "Job failed to be submitted, Return code: $?"
fi
```
