"""
This module is going to contain all duct tape stuff which is required to support
different versions of NetBox together
"""

from validity import config


DEVICE_ROLE_RELATION = "device_role" if config.netbox_version < "3.6.0" else "role"


if config.netbox_version < "3.7.0":
    from extras.webhooks import enqueue_object
    from netbox.context import webhooks_queue as events_queue
    from netbox.models.features import WebhooksMixin as EventRulesMixin
else:
    from extras.events import enqueue_object
    from netbox.context import events_queue
    from netbox.models.features import EventRulesMixin
