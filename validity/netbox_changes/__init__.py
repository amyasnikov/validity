"""
This package contains all duct tape stuff which is required to support
different versions of NetBox together
"""

from functools import partial

from validity import config


if config.netbox_version >= "4.1.0":
    from .current import *
elif config.netbox_version >= "4.0.0":
    from .old import *
else:
    from .oldest import *


def content_types(custom_field):
    return getattr(custom_field, CF_CONTENT_TYPES)


if config.netbox_version < "4.0.0":
    from tenancy.api.nested_serializers import NestedTenantSerializer
else:
    from tenancy.api.serializers import TenantSerializer as __TenantSerializer

    NestedTenantSerializer = partial(__TenantSerializer, nested=True)
