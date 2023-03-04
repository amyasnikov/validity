from functools import partial
from typing import Callable

from dcim.models import Device
from django.db.models import BigIntegerField, Case, Count, F, Manager, OuterRef, QuerySet, Subquery, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast


def get_qs(qs: QuerySet | Manager):
    if isinstance(qs, Manager):
        qs = qs.all()
    return qs


def annotate_bound_git_repos(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return qs.annotate(repo=Cast(KeyTextTransform("git_repo", "tenant__custom_field_data"), BigIntegerField()))


def annotate_serializer(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return (
        qs.annotate(device_s=KeyTextTransform("config_serializer", "custom_field_data"))
        .annotate(
            devtype_s=KeyTextTransform("config_serializer", "device_type__custom_field_data"),
        )
        .annotate(mf_s=KeyTextTransform("config_serializer", "device_type__manufacturer__custom_field_data"))
        .annotate(
            serializer=Case(
                When(device_s__isnull=False, then=Cast(F("device_s"), BigIntegerField())),
                When(devtype_s__isnull=False, then=Cast(F("devtype_s"), BigIntegerField())),
                When(mf_s__isnull=False, then=Cast(F("mf_s"), BigIntegerField())),
            )
        )
    )


def count_devices_per_something(field: str, annotate_func: Callable) -> dict[int | None, int]:
    qs = annotate_func(Device.objects).values(field).annotate(cnt=Count("id", distinct=True))
    result = {}
    for values in qs:
        result[values[field]] = values["cnt"]
    return result


count_devices_per_repo = partial(count_devices_per_something, "repo", annotate_bound_git_repos)
count_devices_per_serializer = partial(count_devices_per_something, "serializer", annotate_serializer)
