from dataclasses import dataclass

from django.db.models import Q
from netbox.models import NetBoxModel


@dataclass
class RelatedObj:
    model: NetBoxModel
    orm_filter: Q
    api_filter: str
