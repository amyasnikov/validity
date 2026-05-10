# NetBox 4.4
from pydoc import locate


BaseModelFilter = locate("netbox.graphql.filter_mixins.BaseFilterMixin")
NetBoxModelFilter = locate("netbox.graphql.filter_mixins.NetBoxModelFilterMixin")
ChoicesType = locate("django.db.models.enums.ChoicesMeta")
