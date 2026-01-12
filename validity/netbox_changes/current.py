# NetBox 4.5
from pydoc import locate

from .old import *


BaseModelFilter = locate("netbox.graphql.filters.BaseModelFilter")
NetBoxModelFilter = locate("netbox.graphql.filters.NetBoxModelFilter")
