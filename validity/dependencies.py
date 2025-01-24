import warnings
from typing import Annotated

from dimi.scopes import Context, Singleton
from django.conf import LazySettings, settings

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
from validity.utils.logger import Logger
from validity.utils.misc import null_request


@di.dependency
def django_settings():
    return settings


@di.dependency(scope=Singleton, add_return_alias=True)
def validity_settings(django_settings: Annotated[LazySettings, django_settings]) -> ValiditySettings:
    settings = django_settings.PLUGINS_CONFIG.get("validity", {})
    if settings.get("runtests_queue"):
        warnings.warn(
            '"runtests_queue" Validity setting is deprecated, use "custom_queues.runtests" instead.',
            FutureWarning,
            stacklevel=1,
        )
    return ValiditySettings.model_validate(settings)


@di.dependency(scope=Context, add_return_alias=True)
def scripts_logger() -> Logger:
    return Logger()


@di.dependency(scope=Singleton, add_return_alias=True)
def backup_backend(vsettings: Annotated[ValiditySettings, ...], logger: Annotated[Logger, ...]) -> BackupBackend:
    return BackupBackend(
        backupers={
            "git": GitBackuper(
                message="",
                author_username=vsettings.integrations.git.author,
                author_email=vsettings.integrations.git.email,
                git_client=DulwichGitClient(),
                logger=logger,
            ),
            "S3": S3Backuper(s3_client=BotoS3Client(max_threads=vsettings.integrations.s3.threads), logger=logger),
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
from validity.scripts import ApplyWorker, CombineWorker, Launcher, SplitWorker, Task, LauncherFactory, perform_backup  # noqa


@di.dependency
def launcher_factory(settings: Annotated[LazySettings, django_settings]) -> LauncherFactory:
    return LauncherFactory(settings.RQ_PARAMS)


@di.dependency(scope=Singleton)
def runtests_launcher(
    vsettings: Annotated[ValiditySettings, validity_settings],
    split_worker: Annotated[SplitWorker, ...],
    apply_worker: Annotated[ApplyWorker, ...],
    combine_worker: Annotated[CombineWorker, ...],
    factory: Annotated[LauncherFactory, launcher_factory],
) -> Launcher:
    from validity.models import ComplianceReport

    return factory.get_launcher(
        "RunTests",
        job_object_factory=lambda _: null_request()(ComplianceReport.objects.create)(),
        queue_name=vsettings.custom_queues.runtests,
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


@di.dependency(scope=Singleton)
def backup_launcher(
    vsettings: Annotated[ValiditySettings, validity_settings],
    factory: Annotated[LauncherFactory, launcher_factory],
) -> Launcher:
    from validity.models import BackupPoint

    return factory.get_launcher(
        "DataSourceBackup",
        job_object_factory=lambda params: BackupPoint.objects.get(pk=params.backuppoint_id),
        queue_name=vsettings.custom_queues.backup,
        tasks=[Task(perform_backup, job_timeout=vsettings.script_timeouts.backup)],
    )
