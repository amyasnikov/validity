import operator
from functools import reduce
from typing import Sequence

from dcim.models import Device
from django.db.models import F, Max, Q
from django_filters import BooleanFilter, ModelMultipleChoiceFilter
from netbox.filtersets import NetBoxModelFilterSet

from validity import models


class SearchMixin:
    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        filter_ = reduce(operator.or_, (Q(**{f"{field}__icontains": value}) for field in self.Meta.search_fields))
        return queryset.filter(filter_)

    class Meta:
        search_fields: Sequence[str]


class ComplianceSelectorFilterSet(SearchMixin, NetBoxModelFilterSet):
    class Meta:
        model = models.ComplianceSelector
        fields = ("id", "name", "filter_operation", "dynamic_pairs")
        search_fields = ("name", "name_filter")


class ComplianceTestFilterSet(NetBoxModelFilterSet):
    selector_id = ModelMultipleChoiceFilter(field_name="selectors", queryset=models.ComplianceSelector.objects.all())

    class Meta:
        model = models.ComplianceTest
        fields = ("id", "name", "selector_id")
        search_fields = ("name", "expression")


class ComplianceTestResultFilterSet(NetBoxModelFilterSet):
    test_id = ModelMultipleChoiceFilter(field_name="test", queryset=models.ComplianceTest.objects.all())
    device_id = ModelMultipleChoiceFilter(field_name="device", queryset=Device.objects.all())
    latest = BooleanFilter(method="filter_latest")

    class Meta:
        model = models.ComplianceTestResult
        fields = ("id", "test_id", "device_id", "passed")
        search_fields = ("test__name", "device__name")

    def filter_latest(self, queryset, name, value):
        return queryset.annotate(max_date=Max("last_updated", filter=Q(test=F("test"), device=F("device")))).filter(
            last_updated=F("max_date")
        )


class GitRepoFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = models.GitRepo
        fields = ("id", "name", "default", "username", "branch", "head_hash")
        search_fields = ("name", "repo_path", "device_config_path")


class ConfigSerializerFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = models.ConfigSerializer
        fields = ('id', 'name')
        search_fields = ('name',)