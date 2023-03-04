from dcim.models import Device
from django.db.models import BigIntegerField, Case, QuerySet, When, Manager, Subquery, OuterRef, Count
from django.db.models.functions import Cast
from django.db.models.fields.json import KeyTextTransform


def get_qs(qs: QuerySet | Manager):
    if isinstance(qs, Manager):
        qs = qs.all()
    return qs


def annotate_bound_git_repos(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return qs.annotate(
            repo=Cast(KeyTextTransform("git_repo", "tenant__custom_field_data"), BigIntegerField())
    )


def count_devices_per_repo() -> dict[int | None, int]:
    qs = annotate_bound_git_repos(Device.objects).values('repo').annotate(cnt=Count('id', distinct=True))
    result = {}
    for values in qs:
        result[values['repo']] = values['cnt']
    return result


def annotate_serializer(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return qs.annotate