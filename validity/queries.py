from dcim.models import Device
from django.db.models import BigIntegerField, Case, QuerySet, When, Manager
from django.db.models.functions import Cast

from .models import GitRepo


def annotate_git_repos(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    if isinstance(qs, Manager):
        qs = qs.all()
    return qs.annotate(
        git_repo=Case(
            When(
                tenant__custom_field_data__git_repo__isnull=False,
                then=Cast("tenant__custom_field_data__git_repo", BigIntegerField()),
            ),
            default=GitRepo.objects.filter(default=True).first()
        )
    )
