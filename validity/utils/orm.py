from typing import Any

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
            for model in self._qs:
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
