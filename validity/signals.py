from django.db.models.signals import pre_delete
from django.dispatch import receiver

from validity.models import ComplianceReport


@receiver(pre_delete, sender=ComplianceReport)
def delete_bound_jobs(sender, instance, **kwargs):
    instance.jobs.all().delete()
