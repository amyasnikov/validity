from functools import partial
from typing import TYPE_CHECKING, Callable, Iterator

from dcim.models import Device
from django.db.models import BigIntegerField, Case, Count, F, Manager, Model, QuerySet, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from netbox.models import RestrictedQuerySet


if TYPE_CHECKING:
    from validity.models import BaseModel


def get_qs(qs: QuerySet | Manager):
    if isinstance(qs, Manager):
        qs = qs.all()
    return qs


def annotate_git_repo_id(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    from validity.models import GitRepo

    qs = get_qs(qs).annotate(
        bound_repo=Cast(KeyTextTransform("git_repo", "tenant__custom_field_data"), BigIntegerField())
    )
    return qs.annotate(
        repo_id=Case(
            When(bound_repo__isnull=False, then=F("bound_repo")),
            default=GitRepo.objects.filter(default=True).values("id")[:1],
            output_field=BigIntegerField(),
        )
    )


def annotate_serializer_id(qs: QuerySet[Device] | Manager[Device]) -> QuerySet[Device]:
    qs = get_qs(qs)
    return (
        qs.annotate(device_s=KeyTextTransform("config_serializer", "custom_field_data"))
        .annotate(
            devtype_s=KeyTextTransform("config_serializer", "device_type__custom_field_data"),
        )
        .annotate(mf_s=KeyTextTransform("config_serializer", "device_type__manufacturer__custom_field_data"))
        .annotate(
            serializer_id=Case(
                When(device_s__isnull=False, then=Cast(F("device_s"), BigIntegerField())),
                When(devtype_s__isnull=False, then=Cast(F("devtype_s"), BigIntegerField())),
                When(mf_s__isnull=False, then=Cast(F("mf_s"), BigIntegerField())),
            )
        )
    )


def annotate_json(qs: QuerySet, field: str, annotate_model: type["BaseModel"]) -> QuerySet:
    return qs.annotate(**{field: annotate_model.objects.filter(pk=f"{field}_id").to_json()})


def annotate_json_repo(qs: QuerySet[Device]) -> QuerySet[Device]:
    from validity.models import GitRepo

    qs = annotate_git_repo_id(qs)
    return annotate_json(qs, "repo", GitRepo)


def annotate_json_serializer(qs: QuerySet[Device]) -> QuerySet[Device]:
    from validity.models import ConfigSerializer

    qs = annotate_serializer_id(qs)
    return annotate_json(qs, "serializer", ConfigSerializer)


def qs_json_iterator(qs: QuerySet, field: str, model: type[Model]) -> Iterator:
    for obj in qs:
        json_object = getattr(obj, field)
        yield model(**json_object)


def count_devices_per_something(field: str, annotate_func: Callable) -> dict[int | None, int]:
    qs = annotate_func(Device.objects).values(field).annotate(cnt=Count("id", distinct=True))
    result = {}
    for values in qs:
        result[values[field]] = values["cnt"]
    return result


count_devices_per_repo = partial(count_devices_per_something, "repo_id", annotate_git_repo_id)
count_devices_per_serializer = partial(count_devices_per_something, "serializer_id", annotate_serializer_id)
