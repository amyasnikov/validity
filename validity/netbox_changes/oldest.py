# NetBox 4.2
from typing import TYPE_CHECKING

from extras.events import enqueue_event, flush_events


if TYPE_CHECKING:
    from validity.models import ComplianceReport
    from validity.scripts.data_models import RequestInfo


def get_logs(job):
    return job.data["log"]


def set_logs(job, logs):
    if not isinstance(job.data, dict):
        job.data = {}
    job.data["log"] = logs


def enqueue(report: "ComplianceReport", request: "RequestInfo"):
    queue = {}
    enqueue_event(queue, report, request.get_user(), request.id, "object_created")
    flush_events(queue.values())
