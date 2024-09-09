# NetBox 4.1
from pydoc import locate as __locate

from .old import *


enqueue_event = __locate("extras.events.enqueue_event")

QUEUE_CREATE_ACTION = "object_created"
