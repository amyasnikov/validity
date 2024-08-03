from typing import Annotated

import django_rq
from dimi.scopes import Singleton
from django.conf import LazySettings, settings
from rq import Callback
from utilities.rqworker import get_queue_for_model

from validity import di
from validity.choices import ConnectionTypeChoices
from validity.models import ComplianceReport
from validity.pollers import NetmikoPoller, RequestsPoller, ScrapliNetconfPoller
from validity.scripts import ApplyWorker, CombineWorker, Launcher, RollbackWorker, SplitWorker, Task
from validity.settings import ValiditySettings


@di.dependency
def django_settings():
    return settings


@di.dependency(scope=Singleton)
def validity_settings(django_settings: Annotated[LazySettings, django_settings]):
    return ValiditySettings.model_validate(django_settings.PLUGINS_CONFIG.get("validity", {}))


@di.dependency(scope=Singleton)
def poller_map():
    return {
        ConnectionTypeChoices.netmiko: NetmikoPoller,
        ConnectionTypeChoices.requests: RequestsPoller,
        ConnectionTypeChoices.scrapli_netconf: ScrapliNetconfPoller,
    }


@di.dependency(scope=Singleton)
def runtests_transaction_template():
    return "ApplyWorker_{job}_{worker}"


@di.dependency(scope=Singleton)
def runtests_launcher(
    vsettings: Annotated[ValiditySettings, validity_settings],
    split_worker: Annotated[SplitWorker, ...],
    apply_worker: Annotated[ApplyWorker, ...],
    combine_worker: Annotated[CombineWorker, ...],
    rollback_worker: Annotated[RollbackWorker, ...],
):
    return Launcher(
        job_name="RunTests",
        job_object_model=ComplianceReport,
        get_queue_fn=lambda model: django_rq.get_queue(get_queue_for_model(model)),
        tasks=[
            Task(split_worker, job_timeout=settings.worker_timeouts.split),
            Task(
                apply_worker,
                job_timeout=settings.worker_timeouts.apply,
                on_failure=Callback(rollback_worker, timeout=settings.worker_timeouts.rollback),
                multi_workers=True,
            ),
            Task(combine_worker, job_timeout=vsettings.worker_timeouts.combine),
        ],
    )
