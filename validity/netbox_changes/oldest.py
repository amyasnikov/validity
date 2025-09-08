# NetBox 4.2


def get_logs(job):
    return job.data["log"]


def set_logs(job, logs):
    if not isinstance(job.data, dict):
        job.data = {}
    job.data["log"] = logs
