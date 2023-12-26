from builtins import *  # noqa

import jq as pyjq

from validity.utils.config import config  # noqa


builtins = [
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytes",
    "callable",
    "chr",
    "complex",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "frozenset",
    "hasattr",
    "hash",
    "hex",
    "int",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "range",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
]


__all__ = ["jq", "config"] + builtins


class jq:
    first = staticmethod(pyjq.first)
    all = staticmethod(pyjq.all)

    def __init__(self, *args, **kwargs) -> None:
        raise TypeError("jq is not callable")
