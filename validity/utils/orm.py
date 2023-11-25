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


class CustomPrefetchMixin(QuerySet):
    """
    Allows to prefetch objects without direct relations
    Many-objects are prefetched as M2MIterator
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.custom_prefetches = {}

    def custom_prefetch(self, field: str, prefetch_qs: QuerySet, many: bool = False):
        pk_field = field + "_id"
        pk_values = self.values_list(pk_field, flat=True)
        if many:
            pk_values = chain.from_iterable(pk_values)
        prefetched_objects = prefetch_qs.filter(pk__in=pk_values)
        self.custom_prefetches[field] = (many, QuerySetMap(prefetched_objects))
        return self

    def _clone(self, *args, **kwargs):
        c = super()._clone(*args, **kwargs)
        c.custom_prefetches = self.custom_prefetches
        return c

    def _fetch_all(self):
        super()._fetch_all()
        for item in self._result_cache:
            if not isinstance(item, self.model):
                continue
            for prefetched_field, (many, qs_dict) in self.custom_prefetches.items():
                prefetch_pk_values = getattr(item, prefetched_field + "_id")
                if many:
                    prefetch_values = M2MIterator(qs_dict[pk] for pk in prefetch_pk_values)
                else:
                    prefetch_values = qs_dict.get(prefetch_pk_values)
                setattr(item, prefetched_field, prefetch_values)
