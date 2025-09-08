# NetBox 4.2


def get_logs(job):
    return job.data["log"]


def set_logs(job, logs):
    if not isinstance(logs.data, dict):
        logs.data = {}
    job.data["log"] = logs
