from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Collection, Iterable

from core.exceptions import SyncError
from django.db.models import Q

from validity.integrations.errors import IntegrationError


if TYPE_CHECKING:
    from validity.models import BackupPoint, VDataSource


def datasource_sync(
    datasources: Iterable["VDataSource"],
    device_filter: Q | None = None,
    threads: int = 10,
    fail_handler: Callable[["VDataSource", Exception], Any] | None = None,
):
    """
    Parrallel sync of multiple Data Sources
    """

    def sync_func(datasource):
        try:
            datasource.sync(device_filter)
        except SyncError as e:
            if fail_handler:
                fail_handler(datasource, e)
            else:
                raise

    with ThreadPoolExecutor(max_workers=threads) as tp:
        any(tp.map(sync_func, datasources))


def bulk_backup(
    backup_points: Collection["BackupPoint"],
    threads: int = 5,
    fail_handler: Callable[["BackupPoint", Exception], Any] | None = None,
) -> None:
    """
    Parallel backup of multiple backup points
    """

    from validity.models import BackupPoint

    def backup(point):
        try:
            point.do_backup()
        except IntegrationError as e:
            if fail_handler:
                fail_handler(point, e)

    with ThreadPoolExecutor(max_workers=threads) as tp:
        any(tp.map(backup, backup_points))
    BackupPoint.objects.bulk_update(backup_points, fields=["last_uploaded", "last_error", "last_status"])
