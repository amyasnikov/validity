from typing import Annotated

import django_rq
from dimi.scopes import Singleton
from django.conf import LazySettings, settings
from utilities.rqworker import get_workers_for_queue

from validity import di
from validity.choices import ConnectionTypeChoices
from validity.pollers import NetmikoPoller, RequestsPoller, ScrapliNetconfPoller
from validity.settings import ValiditySettings
from validity.utils.misc import null_request


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


from validity.scripts import ApplyWorker, CombineWorker, Launcher, SplitWorker, Task  # noqa


@di.dependency
def runtests_worker_count(vsettings: Annotated[ValiditySettings, validity_settings]) -> int:
    return get_workers_for_queue(vsettings.runtests_queue)


@di.dependency(scope=Singleton)
def runtests_launcher(
    vsettings: Annotated[ValiditySettings, validity_settings],
    split_worker: Annotated[SplitWorker, ...],
    apply_worker: Annotated[ApplyWorker, ...],
    combine_worker: Annotated[CombineWorker, ...],
):
    from validity.models import ComplianceReport

    return Launcher(
        job_name="RunTests",
        job_object_factory=null_request()(ComplianceReport.objects.create),
        rq_queue=django_rq.get_queue(vsettings.runtests_queue),
        tasks=[
            Task(split_worker, job_timeout=vsettings.script_timeouts.runtests_split),
            Task(
                apply_worker,
                job_timeout=vsettings.script_timeouts.runtests_apply,
                multi_workers=True,
            ),
            Task(combine_worker, job_timeout=vsettings.script_timeouts.runtests_combine),
        ],
    )
