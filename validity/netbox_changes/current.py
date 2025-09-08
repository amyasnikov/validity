# NetBox 4.4
from .old import *


def get_logs(job):
    return job.log_entries


def set_logs(job, logs):
    job.log_entries = logs
