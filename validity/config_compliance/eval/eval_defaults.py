import ast
import operator
import reprlib

import simpleeval
from simpleeval import DEFAULT_NAMES, DEFAULT_OPERATORS  # noqa


simpleeval.DISALLOW_METHODS += ["delete", "save", "update", "bulk_update", "bulk_create"]
simpleeval.MAX_COMPREHENSION_LENGTH = 100_000
simpleeval.MAX_STRING_LENGTH = 1_000_000

DEFAULT_OPERATORS |= {ast.BitOr: operator.or_, ast.BitAnd: operator.and_}


REPR_DEFAULTS = {"maxlist": 2, "maxdict": 3, "maxlevel": 3, "maxset": 3, "maxlong": 30}

repr_obj = reprlib.Repr()

for prop, value in REPR_DEFAULTS.items():
    setattr(repr_obj, prop, value)


repr_ = repr_obj.repr
