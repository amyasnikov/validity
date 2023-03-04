from functools import partial
from types import GenericAlias
from typing import TYPE_CHECKING, Iterator, TypeVar

from dcim.models import Device
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import BigIntegerField, Case, Count, F, OuterRef, Q, QuerySet, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from netbox.models import RestrictedQuerySet


if TYPE_CHECKING:
    from validity.models import BaseModel


_QS = TypeVar("_QS", bound=QuerySet)


def annotate_json(qs: _QS, field: str, annotate_model: type["BaseModel"]) -> _QS:
    return qs.annotate(**{field: annotate_model.objects.filter(pk=OuterRef(f"{field}_id")).as_json()})


class DeviceQS(RestrictedQuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None) -> None:
        if model is None:
            qs = Device.objects.all()
            super().__init__(qs.model, qs._query, qs._db, qs._hints)
        else:
            super().__init__(model, query, using, hints)

    def annotate_git_repo_id(self: _QS) -> _QS:
        from validity.models import GitRepo

        return self.annotate(
            bound_repo=Cast(KeyTextTransform("git_repo", "tenant__custom_field_data"), BigIntegerField())
        ).annotate(
            repo_id=Case(
                When(bound_repo__isnull=False, then=F("bound_repo")),
                default=GitRepo.objects.filter(default=True).values("id")[:1],
                output_field=BigIntegerField(),
            )
        )

    def annotate_serializer_id(self: _QS) -> _QS:
        return (
            self.annotate(device_s=KeyTextTransform("config_serializer", "custom_field_data"))
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

    def annotate_json_namesets(self: _QS) -> _QS:
        from validity.models import NameSet

        namesets = NameSet.objects.filter(Q(_global=True) | Q(serializers__pk=OuterRef("serializer_id"))).as_json()
        return self.annotate_serializer_id().annotate(namesets=ArraySubquery(namesets))

    def annotate_json_repo(self: _QS) -> _QS:
        from validity.models import GitRepo

        qs = self.annotate_git_repo_id()
        return annotate_json(qs, "repo", GitRepo)

    def annotate_json_serializer(self: _QS) -> _QS:
        from validity.models import ConfigSerializer

        qs = self.annotate_serializer_id()
        return annotate_json(qs, "serializer", ConfigSerializer)

    def json_iterator(self, *fields: str) -> Iterator:
        from validity.models import ConfigSerializer, GitRepo, NameSet

        models = {"repo": GitRepo, "serializer": ConfigSerializer, "namesets": list[NameSet]}
        for device in self:
            for field in fields:
                model = models[field]
                json_repr = getattr(device, field, None)
                if json_repr is None:
                    continue
                if isinstance(model, GenericAlias):
                    model = model.__args__[0]
                    json_obj = [model(obj) for obj in json_repr]
                else:
                    json_obj = model(**json_repr)
                setattr(device, field, json_obj)
            yield device


def count_devices_per_something(field: str, annotate_method: str) -> dict[int | None, int]:
    qs = getattr(DeviceQS(), annotate_method)().values(field).annotate(cnt=Count("id", distinct=True))
    result = {}
    for values in qs:
        result[values[field]] = values["cnt"]
    return result


count_devices_per_repo = partial(count_devices_per_something, "repo_id", "annotate_git_repo_id")
count_devices_per_serializer = partial(count_devices_per_something, "serializer_id", "annotate_serializer_id")
