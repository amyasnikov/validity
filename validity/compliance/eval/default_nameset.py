from builtins import *  # noqa

from validity.models import VDevice
from validity.utils.orm import model_to_proxy
from validity.utils.json import jq  # noqa


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


def state(device):
    # state() implies presence of "_data_source" and "_poller" global variables
    # which are gonna be set by RunTests script
    vdevice = model_to_proxy(device, VDevice)
    vdevice.data_source = _data_source  # noqa
    vdevice._poller = _poller  # noqa
    return vdevice.state


def config(device):
    return state(device).config
