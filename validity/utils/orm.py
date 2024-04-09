from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Generic, Iterable, Iterator, TypeVar

from django.db.models import Model, QuerySet


M = TypeVar("M", bound=Model)
N = TypeVar("N", bound=Model)


class QuerySetMap(Generic[M]):
    """
    Lazy pk:model dict which hits the DB when first queried
    """

    def __init__(self, qs: QuerySet[M], attribute: str = "pk"):
        self._qs = qs
        self._attribute = attribute
        self._evaluated = False
        self._map = {}

    def _evaluate(self):
        if not self._evaluated:
            qs = self._qs if self._qs._result_cache is not None else self._qs.iterator(chunk_size=2000)
            for model in qs:
                self._map[getattr(model, self._attribute)] = model
            self._evaluated = True

    def __getitem__(self, key):
        self._evaluate()
        return self._map[key]

    def __contains__(self, key):
        self._evaluate()
        return key in self._map

    def get(self, key, default=None):
        self._evaluate()
        return self._map.get(key, default)

    def keys(self):
        self._evaluate()
        return self._map.keys()

    @property
    def model(self):
        return self._qs.model


class M2MIterator(Generic[M]):
    """
    This class mimics lazy handling of the QuerySet
    """

    def __init__(self, iterable: Iterable[M]) -> None:
        self.iterable = iterable
        self.cache = None

    def all(self) -> Iterator[M]:
        if self.cache is None:
            self.cache = list(self.iterable)
        yield from self.cache


@dataclass
class CustomPrefetch:
    field: str
    pk_field: str
    remote_pk_field: str
    qs: QuerySet
    many: bool
    postfetch: bool = False

    def _qs_map_from_keys(self, pk_values: Iterable[int | str | Iterable[int | str]]) -> QuerySetMap:
        if self.many:
            pk_values = chain.from_iterable(pk_values)
        return QuerySetMap(self.qs.filter(**{f"{self.remote_pk_field}__in": pk_values}), attribute=self.remote_pk_field)

    def get_prefetch_qs_map(self, main_queryset: QuerySet) -> QuerySetMap:
        pk_values = main_queryset.values_list(self.pk_field, flat=True)
        return self._qs_map_from_keys(pk_values)

    def get_postfetch_qs_map(self, main_queryset: QuerySet):
        pk_values = (getattr(obj, self.pk_field) for obj in main_queryset._result_cache)
        return self._qs_map_from_keys(pk_values)

    def get_qs_map(self, main_queryset: QuerySet):
        return self.get_postfetch_qs_map(main_queryset) if self.postfetch else self.get_prefetch_qs_map(main_queryset)

    def get_value_storage(self, main_queryset: QuerySet) -> "ValueStorage":
        qs_map = self.get_qs_map(main_queryset)
        return ValueStorage(self.field, self.pk_field, qs_map, self.many)


@dataclass
class ValueStorage:
    field: str
    pk_field: str
    qs_map: QuerySetMap
    many: bool

    def get_joined_value(self, instance: Model) -> Model | Iterable[Model]:
        pk_value = getattr(instance, self.pk_field)
        if self.many:
            return M2MIterator(self.qs_map[pk] for pk in pk_value)
        else:
            return self.qs_map.get(pk_value)

    def setup_field(self, instance: Model) -> None:
        joined_value = self.get_joined_value(instance)
        setattr(instance, self.field, joined_value)


class CustomPrefetchMixin(QuerySet):
    """
    Allows to prefetch objects without direct relations
    Many-objects are prefetched as M2MIterator
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.custom_prefetches = []

    def custom_prefetch(
        self, field: str, prefetch_qs: QuerySet, many: bool = False, pk_field: str = "", remote_pk_field: str = "pk"
    ):
        pk_field = pk_field or field + "_id"
        self.custom_prefetches.append(CustomPrefetch(field, pk_field, remote_pk_field, prefetch_qs, many))
        return self

    custom_prefetch.queryset_only = True

    def custom_postfetch(
        self, field: str, postfetch_qs: QuerySet, many: bool = False, pk_field: str = "", remote_pk_field: str = "pk"
    ):
        """
        Allows to use prefetch with runtime model attributes (like dynamically set by .set_attribute)
        """
        self.custom_prefetch(field, postfetch_qs, many, pk_field, remote_pk_field)
        self.custom_prefetches[-1].postfetch = True
        return self

    custom_postfetch.queryset_only = True

    def _clone(self, *args, **kwargs):
        c = super()._clone(*args, **kwargs)
        c.custom_prefetches = self.custom_prefetches.copy()
        return c

    def _fetch_all(self):
        super()._fetch_all()
        for custom_prefetch in self.custom_prefetches:
            value_storage = custom_prefetch.get_value_storage(self)
            for model_instance in self._result_cache:
                value_storage.setup_field(model_instance)


class SetAttributesMixin(QuerySet):
    """
    Allows to define aux qs-level attributes which will be assigned to model instances
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._aux_attributes = {}

    def _clone(self, *args, **kwargs):
        c = super()._clone(*args, **kwargs)
        c._aux_attributes = self._aux_attributes
        return c

    def bind_attributes(self, instance):
        for attr, attr_value in self._aux_attributes.items():
            setattr(instance, attr, attr_value)

    def _fetch_all(self):
        super()._fetch_all()
        for item in self._result_cache:
            if isinstance(item, self.model):
                self.bind_attributes(item)

    def set_attribute(self, name, value):
        self._aux_attributes[name] = value
        return self


def model_to_proxy(model: Model, proxy_type: type[M]) -> M:
    """
    Converts model to its proxy type (e.g. Device to VDevice)
    """
    new_model = proxy_type()
    new_model.__dict__ = model.__dict__.copy()
    return new_model
