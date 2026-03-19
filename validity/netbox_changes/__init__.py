"""
This package contains all duct tape stuff which is required to support
different versions of NetBox together
"""

from pydoc import locate

from strawberry_django import FilterLookup

from validity import config


StrFilterLookup = locate("strawberry_django.StrFilterLookup") if config.netbox_version >= "4.5.4" else FilterLookup[str]

if config.netbox_version >= "4.5.0":
    from .current import *
elif config.netbox_version >= "4.4.0":
    from .old import *
else:
    from .oldest import *
