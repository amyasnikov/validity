from builtins import *  # noqa

import jq as pyjq

from validity.models import VDevice


builtins = [
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytes",
    "callable",
    "classmethod",
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
    "property",
    "range",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "tuple",
    "zip",
]


__all__ = ["jq", "config", "state"] + builtins


class jq:
    first = staticmethod(pyjq.first)
    all = staticmethod(pyjq.all)

    def __init__(self, *args, **kwargs) -> None:
        raise TypeError("jq is not callable")


def state(device):
    # state() implies presence of "_data_source" and "_poller" global variables
    # which are gonna be set by RunTests script
    vdevice = VDevice()
    vdevice.__dict__ = device.__dict__.copy()
    vdevice.data_source = _data_source  # noqa
    vdevice._poller = _poller  # noqa
    return vdevice.state


def config(device):
    return state(device).config
