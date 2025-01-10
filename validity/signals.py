from core.signals import post_sync
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from validity.models import BackupPoint, ComplianceReport
from validity.utils.bulk import bulk_backup


@receiver(pre_delete, sender=ComplianceReport)
def delete_bound_jobs(sender, instance, **kwargs):
    instance.jobs.all().delete()


@receiver(post_sync)
def backup_datasource(sender, instance, **kwargs):
    if getattr(instance, "permit_backup", True):
        backup_points = BackupPoint.objects.filter(backup_after_sync=True, data_source=instance)
        bulk_backup(backup_points)
