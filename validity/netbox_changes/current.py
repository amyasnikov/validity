# NetBox 4.4
from typing import TYPE_CHECKING

from .old import *


if TYPE_CHECKING:
    from validity.models import ComplianceReport
    from validity.scripts.data_models import RequestInfo


def get_logs(job):
    return job.log_entries


def set_logs(job, logs):
    job.log_entries = logs


def enqueue(report: "ComplianceReport", request: "RequestInfo"):
    queue = {}
    enqueue_event(queue, report, request, "object_created")
    flush_events(queue.values())
