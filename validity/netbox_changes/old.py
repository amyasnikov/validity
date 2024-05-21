# NetBox 3.7
from pydoc import locate as __locate

from .oldest import *


enqueue_object = __locate("extras.events.enqueue_object")
events_queue = __locate("netbox.context.events_queue")
EventRulesMixin = __locate("netbox.models.features.EventRulesMixin")
