from typing import Annotated

import django_rq
from dimi.scopes import Singleton
from django.conf import LazySettings, settings
from rq import Callback

from validity import di
from validity.choices import ConnectionTypeChoices
from validity.pollers import NetmikoPoller, RequestsPoller, ScrapliNetconfPoller
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


from validity.scripts import ApplyWorker, CombineWorker, Launcher, RollbackWorker, SplitWorker, Task  # noqa


@di.dependency(scope=Singleton)
def runtests_launcher(
    vsettings: Annotated[ValiditySettings, validity_settings],
    split_worker: Annotated[SplitWorker, ...],
    apply_worker: Annotated[ApplyWorker, ...],
    combine_worker: Annotated[CombineWorker, ...],
    rollback_worker: Annotated[RollbackWorker, ...],
):
    from validity.models import ComplianceReport

    return Launcher(
        job_name="RunTests",
        job_object_model=ComplianceReport,
        rq_queue=django_rq.get_queue(vsettings.runtests_queue),
        tasks=[
            Task(split_worker, job_timeout=vsettings.script_timeouts.runtests_split),
            Task(
                apply_worker,
                job_timeout=vsettings.script_timeouts.runtests_apply,
                on_failure=Callback(rollback_worker.as_func(), timeout=vsettings.script_timeouts.runtests_rollback),
                multi_workers=True,
            ),
            Task(combine_worker, job_timeout=vsettings.script_timeouts.runtests_combine),
        ],
    )
