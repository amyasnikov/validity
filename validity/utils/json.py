import copy
from typing import Callable, Collection, Protocol

import jq as pyjq


Json = dict[str, "Json"] | list["Json"] | int | float | str | None


class TransformFn(Protocol):
    def __call__(self, key: int | str, value: Json, /) -> tuple[int | str, Json] | None: ...


def transform_json(data: Json, match_fn: Callable[[int | str, Json], bool], transform_fn: TransformFn) -> Json:
    """
    Traverse JSON-like struct recursively and apply "tranform_fn" to keys and values matched by "match_fn"
    """

    def transform(data_item: Json) -> None:
        if isinstance(data_item, str) or not isinstance(data_item, Collection):
            return
        iterator = data_item.items() if isinstance(data_item, dict) else enumerate(data_item)
        delete_keys = []
        new_values = {}
        for key, value in iterator:
            if match_fn(key, value):
                result = transform_fn(key, value)
                if result is None:
                    delete_keys.append(key)
                    continue
                new_key, new_value = result
                if new_key == key:
                    data_item[key] = new_value
                else:
                    delete_keys.append(key)
                    new_values[new_key] = new_value
            elif isinstance(value, Collection):
                transform(value)
        for del_key in delete_keys:
            del data_item[del_key]
        for new_key, new_value in new_values.items():
            data_item[new_key] = new_value

    data_copy = copy.deepcopy(data)
    transform(data_copy)
    return data_copy


class jq:
    _extra_functions = [
        # ensures that expression at "pth" is an array
        'def mkarr(pth): . | pth as $tgt | . | pth = if $tgt | type != "array" then [$tgt] else $tgt end',
        # recursively converts all number-like strings to numbers
        "def mknum(pth):. | pth as $tgt | . | pth = "
        '($tgt | walk(if type == "string" and test("[+-]?([0-9]*[.])?[0-9]+") then . | tonumber else . end))',
        'def mknum: walk(if type == "string" and test("[+-]?([0-9]*[.])?[0-9]+") then . | tonumber else . end)',
    ]

    @classmethod
    def _add_extra_functions(cls, expression):
        extra_funcs = ";".join(cls._extra_functions)
        return f"{extra_funcs};{expression}"

    @classmethod
    def first(cls, expression, data):
        return pyjq.first(cls._add_extra_functions(expression), data)

    @classmethod
    def all(cls, expression, data):
        return pyjq.all(cls._add_extra_functions(expression), data)

    @classmethod
    def compile(cls, expression):
        return pyjq.compile(cls._add_extra_functions(expression))

    def __init__(self, *args, **kwargs) -> None:
        raise TypeError("jq is not callable")
