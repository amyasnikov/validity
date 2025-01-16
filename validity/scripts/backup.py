from validity.integrations.errors import IntegrationError
from validity.utils.misc import md_link
from .data_models import FullBackUpParams
from .exceptions import AbortScript
from .keeper import JobKeeper


def perform_backup(params: FullBackUpParams):
    """
    Script to do the backup using one single Backup Point
    """
    job = params.get_job()
    with JobKeeper(job) as keeper:
        backup_point = job.object
        try:
            backup_point.do_backup()
            ds_link = md_link(backup_point.data_source)
            keeper.logger.success(
                f"{ds_link} data source has been backed up using {md_link(backup_point)} backup point"
            )
        except IntegrationError as e:
            raise AbortScript(str(e)) from e
        finally:
            backup_point.save(update_fields=["last_uploaded", "last_status", "last_error"])
