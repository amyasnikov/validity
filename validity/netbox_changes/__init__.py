"""
This package contains all duct tape stuff which is required to support
different versions of NetBox together
"""

from validity import config


if config.netbox_version >= "4.4.0":
    from .current import *
elif config.netbox_version >= "4.3.0":
    from .old import *
else:
    from .oldest import *
