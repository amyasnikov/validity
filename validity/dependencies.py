from typing import Annotated

from dimi.scopes import Singleton
from django.conf import LazySettings, settings
from django_rq.queues import DjangoRQ, get_redis_connection
from redis import Redis
from rq import Queue, Worker
from rq.job import Job

from validity import di
from validity.compliance.serialization import (
    SerializationBackend,
    serialize_ros,
    serialize_textfsm,
    serialize_ttp,
    serialize_xml,
    serialize_yaml,
)
from validity.data_backup import BackupBackend, GitBackuper, S3Backuper
from validity.integrations.git import DulwichGitClient
from validity.integrations.s3 import BotoS3Client
from validity.pollers import NetmikoPoller, RequestsPoller, ScrapliNetconfPoller
from validity.settings import PollerInfo, ValiditySettings
from validity.utils.misc import null_request


@di.dependency
def django_settings():
    return settings


@di.dependency(scope=Singleton, add_return_alias=True)
def validity_settings(django_settings: Annotated[LazySettings, django_settings]) -> ValiditySettings:
    return ValiditySettings.model_validate(django_settings.PLUGINS_CONFIG.get("validity", {}))


@di.dependency(scope=Singleton, add_return_alias=True)
def backup_backend(vsettings: Annotated[ValiditySettings, ...]) -> BackupBackend:
    return BackupBackend(
        backupers={
            "git": GitBackuper(
                message="",
                author_username=vsettings.integrations.git.author,
                author_email=vsettings.integrations.git.email,
                git_client=DulwichGitClient(),
            ),
            "S3": S3Backuper(s3_client=BotoS3Client(max_threads=vsettings.integrations.s3.threads)),
        }
    )


@di.dependency(scope=Singleton, add_return_alias=True)
def serialization_backend() -> SerializationBackend:
    return SerializationBackend(
        extraction_methods={
            "YAML": serialize_yaml,
            "ROUTEROS": serialize_ros,
            "TTP": serialize_ttp,
            "TEXTFSM": serialize_textfsm,
            "XML": serialize_xml,
        }
    )


@di.dependency(scope=Singleton)
def pollers_info(custom_pollers: Annotated[list[PollerInfo], "validity_settings.custom_pollers"]) -> list[PollerInfo]:
    return [
        PollerInfo(klass=NetmikoPoller, name="netmiko", verbose_name="netmiko", color="blue", command_types=["CLI"]),
        PollerInfo(
            klass=RequestsPoller, name="requests", verbose_name="requests", color="info", command_types=["json_api"]
        ),
        PollerInfo(
            klass=ScrapliNetconfPoller,
            name="scrapli_netconf",
            verbose_name="scrapli_netconf",
            color="orange",
            command_types=["netconf"],
        ),
    ] + custom_pollers


import validity.pollers.factory  # noqa
from validity.scripts import ApplyWorker, CombineWorker, Launcher, SplitWorker, Task  # noqa


@di.dependency
def runtests_queue_config(
    settings: Annotated[LazySettings, django_settings], vsettings: Annotated[ValiditySettings, validity_settings]
) -> dict:
    return settings.RQ_QUEUES.get(vsettings.runtests_queue, settings.RQ_PARAMS)


@di.dependency
def runtests_redis_connection(queue_config: Annotated[dict, runtests_queue_config]) -> Redis:
    return get_redis_connection(queue_config)


@di.dependency
def runtests_queue(
    vsettings: Annotated[ValiditySettings, validity_settings],
    config: Annotated[dict, runtests_queue_config],
    connection: Annotated[Redis, runtests_redis_connection],
) -> Queue:
    is_async = config.get("ASYNC", True)
    default_timeout = config.get("DEFAULT_TIMEOUT")
    return DjangoRQ(
        vsettings.runtests_queue,
        default_timeout=default_timeout,
        connection=connection,
        is_async=is_async,
        job_class=Job,
    )


@di.dependency
def runtests_worker_count(
    connection: Annotated[Redis, runtests_redis_connection], queue: Annotated[Queue, runtests_queue]
) -> int:
    return Worker.count(connection=connection, queue=queue)


@di.dependency(scope=Singleton)
def runtests_launcher(
    vsettings: Annotated[ValiditySettings, validity_settings],
    split_worker: Annotated[SplitWorker, ...],
    apply_worker: Annotated[ApplyWorker, ...],
    combine_worker: Annotated[CombineWorker, ...],
    queue: Annotated[Queue, runtests_queue],
):
    from validity.models import ComplianceReport

    return Launcher(
        job_name="RunTests",
        job_object_factory=null_request()(ComplianceReport.objects.create),
        rq_queue=queue,
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
