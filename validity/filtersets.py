import operator
from functools import reduce
from typing import Sequence

from dcim.filtersets import DeviceFilterSet
from dcim.models import Device, DeviceRole, DeviceType, Location, Manufacturer, Platform, Site
from django.db.models import Q
from django_filters import BooleanFilter, ChoiceFilter, ModelMultipleChoiceFilter
from extras.models import Tag
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.models import Tenant

from validity import models
from validity.choices import SeverityChoices
from validity.netbox_changes import DEVICE_ROLE_RELATION


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
    datasource_id = ModelMultipleChoiceFilter(field_name="data_source", queryset=models.VDataSource.objects.all())

    class Meta:
        model = models.ComplianceTest
        fields = ("id", "name", "selector_id", "severity", "datasource_id")
        search_fields = ("name", "description", "expression")


class ComplianceTestResultFilterSet(SearchMixin, NetBoxModelFilterSet):
    test_id = ModelMultipleChoiceFilter(field_name="test", queryset=models.ComplianceTest.objects.all())
    device_id = ModelMultipleChoiceFilter(field_name="device", queryset=Device.objects.all())
    report_id = ModelMultipleChoiceFilter(field_name="report", queryset=models.ComplianceReport.objects.all())
    latest = BooleanFilter(method="filter_latest")
    severity = ChoiceFilter(field_name="test__severity", choices=SeverityChoices.choices)
    device_type_id = ModelMultipleChoiceFilter(field_name="device__device_type", queryset=DeviceType.objects.all())
    manufacturer_id = ModelMultipleChoiceFilter(
        field_name="device__device_type__manufacturer", queryset=Manufacturer.objects.all()
    )
    device_role_id = ModelMultipleChoiceFilter(
        field_name=f"device__{DEVICE_ROLE_RELATION}", queryset=DeviceRole.objects.all()
    )
    tenant_id = ModelMultipleChoiceFilter(field_name="device__tenant", queryset=Tenant.objects.all())
    platform_id = ModelMultipleChoiceFilter(field_name="device__platform", queryset=Platform.objects.all())
    location_id = ModelMultipleChoiceFilter(field_name="device__location", queryset=Location.objects.all())
    site_id = ModelMultipleChoiceFilter(field_name="device__site", queryset=Site.objects.all())
    test_tag_id = ModelMultipleChoiceFilter(field_name="test__tags", queryset=Tag.objects.all())
    tag = None

    class Meta:
        model = models.ComplianceTestResult
        fields = (
            "id",
            "test_id",
            "device_id",
            "passed",
            "latest",
            "severity",
            "device_type_id",
            "manufacturer_id",
            "device_role_id",
            "tenant_id",
            "platform_id",
            "location_id",
            "site_id",
        )
        search_fields = ("test__name", "device__name")

    def filter_latest(self, queryset, name, value):
        return queryset.only_latest(exclude=not value)


class SerializerFilterSet(SearchMixin, NetBoxModelFilterSet):
    datasource_id = ModelMultipleChoiceFilter(field_name="data_source", queryset=models.VDataSource.objects.all())

    class Meta:
        model = models.Serializer
        fields = ("id", "name", "extraction_method", "datasource_id")
        search_fields = ("name",)


class NameSetFilterSet(SearchMixin, NetBoxModelFilterSet):
    datasource_id = ModelMultipleChoiceFilter(field_name="data_source", queryset=models.VDataSource.objects.all())

    class Meta:
        model = models.NameSet
        fields = ("id", "name", "_global")
        search_fields = ("name", "description", "definitions")

    @classmethod
    def get_filters(cls):
        filters = super().get_filters()
        filters["global"] = filters.pop("_global")
        return filters


class DeviceReportFilterSet(DeviceFilterSet):
    compliance_passed = BooleanFilter()


class PollerFilterSet(SearchMixin, NetBoxModelFilterSet):
    class Meta:
        model = models.Poller
        fields = ("id", "name", "connection_type")
        search_fields = ("name",)


class CommandFilterSet(SearchMixin, NetBoxModelFilterSet):
    serializer_id = ModelMultipleChoiceFilter(field_name="serializer", queryset=models.Serializer.objects.all())
    poller_id = ModelMultipleChoiceFilter(field_name="pollers", queryset=models.Poller.objects.all())

    class Meta:
        model = models.Command
        fields = ("id", "name", "label", "type", "retrieves_config", "serializer_id", "poller_id")
        search_fields = ("name", "label")
