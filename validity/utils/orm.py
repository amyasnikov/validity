from dataclasses import dataclass
from itertools import chain
from typing import Any, Generic, Iterable, Iterator, TypeVar

from django.db.models import F, Func, QuerySet, TextField


class RegexpReplace(Func):
    function = "REGEXP_REPLACE"

    def __init__(self, source: F, pattern: str, replacement_string: str, flags: str = "", **extra: Any) -> None:
        extra.setdefault("output_field", TextField())
        expressions = [source, pattern, replacement_string]
        if flags:
            expressions.append(flags)
        super().__init__(*expressions, **extra)


class QuerySetMap:
    """
    Lazy pk:model dict which hits the DB when first queried
    """

    def __init__(self, qs: QuerySet, attribute: str = "pk"):
        self._qs = qs
        self._attribute = attribute
        self._evaluated = False
        self._map = {}

    def _evaluate(self):
        if not self._evaluated:
            for model in self._qs.iterator(chunk_size=2000):
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

    @property
    def model(self):
        return self._qs.model


M = TypeVar("M")


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
    qs: QuerySet
    many: bool

    pk_field = property(lambda self: self.field + "_id")

    def get_qs_map(self, main_queryset: QuerySet) -> QuerySetMap:
        pk_values = main_queryset.values_list(self.pk_field, flat=True)
        if self.many:
            pk_values = chain.from_iterable(pk_values)
        return QuerySetMap(self.qs.filter(pk__in=pk_values))


class CustomPrefetchMixin(QuerySet):
    """
    Allows to prefetch objects without direct relations
    Many-objects are prefetched as M2MIterator
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.custom_prefetches = []

    def custom_prefetch(self, field: str, prefetch_qs: QuerySet, many: bool = False):
        self.custom_prefetches.append(CustomPrefetch(field, prefetch_qs, many))
        return self

    custom_prefetch.queryset_only = True

    def _clone(self, *args, **kwargs):
        c = super()._clone(*args, **kwargs)
        c.custom_prefetches = self.custom_prefetches.copy()
        return c

    def _fetch_all(self):
        super()._fetch_all()
        qs_dicts = {custom_pf.field: custom_pf.get_qs_map(self) for custom_pf in self.custom_prefetches}
        for item in self._result_cache:
            if not isinstance(item, self.model):
                continue
            for custom_prefetch in self.custom_prefetches:
                prefetch_pk_values = getattr(item, custom_prefetch.pk_field)
                qs_dict = qs_dicts[custom_prefetch.field]
                if custom_prefetch.many:
                    prefetch_values = M2MIterator(qs_dict[pk] for pk in prefetch_pk_values)
                else:
                    prefetch_values = qs_dict.get(prefetch_pk_values)
                setattr(item, custom_prefetch.field, prefetch_values)
