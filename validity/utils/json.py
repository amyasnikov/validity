import copy
from typing import Callable, Collection, Protocol


Json = dict[str, "Json"] | list["Json"] | int | float | str | None


class TransformFn(Protocol):
    def __call__(self, key: int | str, value: Json) -> tuple[int | str, Json] | None:
        ...


def transform_json(data: Json, match_fn: Callable[[int | str, Json], bool], transform_fn: TransformFn) -> Json:
    """
    Traverse JSON-like struct recursively and apply "tranform_fn" to keys and values matched by "match_fn"
    """

    def transform(data_item: Json) -> None:
        if isinstance(data_item, str) or not isinstance(data_item, Collection):
            return
        iterator = data_item.items() if isinstance(data_item, dict) else enumerate(data_item)
        for key, value in iterator:
            if match_fn(key, value):
                result = transform_fn(key, value)
                if result is None:
                    del data_item[key]
                    continue
                new_key, new_value = result
                if new_key == key:
                    data_item[key] = new_value
                else:
                    del data_item[key]
                    data_item[new_key] = new_value
            elif isinstance(value, Collection):
                transform(value)

    data_copy = copy.deepcopy(data)
    transform(data_copy)
    return data_copy
