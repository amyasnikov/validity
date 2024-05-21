import strawberry_django
from netbox.graphql.filter_mixins import BaseFilterMixin, autotype_decorator

from validity import filtersets


def adapt_to_strawberry(filterset):
    strawberry_filter = type(filterset.__name__.removesuffix("Set"), (BaseFilterMixin,), {})
    strawberry_filter = autotype_decorator(filterset)(strawberry_filter)
    return strawberry_django.filter(filterset.Meta.model, lookups=True)(strawberry_filter)


ComplianceSelectorFilter = adapt_to_strawberry(filtersets.ComplianceSelectorFilterSet)
ComplianceTestFilter = adapt_to_strawberry(filtersets.ComplianceTestFilterSet)
ComplianceTestResultFilter = adapt_to_strawberry(filtersets.ComplianceTestResultFilterSet)
SerializerFilter = adapt_to_strawberry(filtersets.SerializerFilterSet)
NameSetFilter = adapt_to_strawberry(filtersets.NameSetFilterSet)
PollerFilter = adapt_to_strawberry(filtersets.PollerFilterSet)
CommandFilter = adapt_to_strawberry(filtersets.CommandFilterSet)
