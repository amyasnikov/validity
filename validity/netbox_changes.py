"""
This module is going to contain all duct tape stuff which is required to support
newer versions of NetBox
"""
from validity import config


DEVICE_ROLE_RELATION = "device_role" if config.netbox_version < "3.6.0" else "role"
