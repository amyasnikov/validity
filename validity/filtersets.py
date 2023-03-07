import operator
from functools import reduce
from typing import Sequence

from dcim.models import Device
from django.db.models import Q
from django_filters import BooleanFilter, ChoiceFilter, ModelMultipleChoiceFilter
from netbox.filtersets import NetBoxModelFilterSet

from validity import models
from validity.choices import SeverityChoices


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


class ComplianceTestFilterSet(SearchMixin, NetBoxModelFilterSet):
    selector_id = ModelMultipleChoiceFilter(field_name="selectors", queryset=models.ComplianceSelector.objects.all())
    repo_id = ModelMultipleChoiceFilter(field_name="repo", queryset=models.GitRepo.objects.all())

    class Meta:
        model = models.ComplianceTest
        fields = ("id", "name", "selector_id", "severity", "repo_id", "file_path")
        search_fields = ("name", "description", "expression")


class ComplianceTestResultFilterSet(SearchMixin, NetBoxModelFilterSet):
    test_id = ModelMultipleChoiceFilter(field_name="test", queryset=models.ComplianceTest.objects.all())
    device_id = ModelMultipleChoiceFilter(field_name="device", queryset=Device.objects.all())
    latest = BooleanFilter(method="filter_latest")
    test__severity = ChoiceFilter(field_name="test__severity", choices=SeverityChoices.choices)
    tag = None

    class Meta:
        model = models.ComplianceTestResult
        fields = ("id", "test_id", "device_id", "passed", "latest", "test__severity")
        search_fields = ("test__name", "device__name")

    def filter_latest(self, queryset, name, value):
        if value:
            queryset = queryset.only_latest()
        return queryset


class GitRepoFilterSet(SearchMixin, NetBoxModelFilterSet):
    class Meta:
        model = models.GitRepo
        fields = ("id", "name", "default", "username", "branch", "head_hash")
        search_fields = ("name", "repo_path", "device_config_path")


class ConfigSerializerFilterSet(SearchMixin, NetBoxModelFilterSet):
    repo_id = ModelMultipleChoiceFilter(field_name="repo", queryset=models.GitRepo.objects.all())

    class Meta:
        model = models.ConfigSerializer
        fields = ("id", "name", "extraction_method", "repo_id", "file_path")
        search_fields = ("name",)


class NameSetFilterSet(SearchMixin, NetBoxModelFilterSet):
    repo_id = ModelMultipleChoiceFilter(field_name="repo", queryset=models.GitRepo.objects.all())

    class Meta:
        model = models.NameSet
        fields = ("id", "name", "_global", "repo_id", "file_path")
        search_fields = ("name", "description", "definitions")
