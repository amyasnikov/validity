import functools
from typing import Any, Dict, Iterable, Iterator

from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django_tables2 import SingleTableMixin
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from validity import filtersets, forms, models, tables
from validity.choices import DeviceGroupByChoices, SeverityChoices
from .base import FilterViewWithForm, TestResultBaseView


class ComplianceReportListView(generic.ObjectListView):
    queryset = models.ComplianceReport.objects.annotate_result_stats().count_devices_and_tests().order_by("-created")
    table = tables.ComplianceReportTable

    def get_table(self, data, request, bulk_actions=True):
        table = super().get_table(data, request, bulk_actions)
        table.exclude += ("groupby_value",)
        return table


@register_model_view(models.ComplianceReport)
class ComplianceReportView(generic.ObjectView):
    model = models.ComplianceReport
    queryset = models.ComplianceReport.objects.annotate_result_stats().count_devices_and_tests()

    def get_table(self, groupby_qs):
        table = tables.ComplianceReportTable(data=groupby_qs)
        table.exclude += ("id", "created", "test_count")
        return table

    def transform_groupby_qs(self, groupby_qs: Iterable[dict], groupby_field: DeviceGroupByChoices) -> Iterator[dict]:
        pk_field = f"results__{groupby_field.pk_field()}"
        name_field = f"results__{groupby_field}"
        for item in groupby_qs:
            item["viewname"] = groupby_field.viewname()
            item["groupby_value"] = item[name_field]
            item["groupby_pk"] = item[pk_field]
            yield item

    def get_extra_context(self, request, instance):
        groupby_field = DeviceGroupByChoices.member(request.GET.get("group_by"))
        form_initial = {"group_by": groupby_field.value} if groupby_field else {}
        form = forms.ReportGroupByForm(initial=form_initial)
        context: dict[str, Any] = {"groupby_form": form}
        if groupby_field:
            groupby_qs = (
                self.model.objects.filter(pk=instance.pk).annotate_result_stats(groupby_field).count_devices_and_tests()
            )
            table = self.get_table(self.transform_groupby_qs(groupby_qs, groupby_field))
            table.configure(request)
            context["groupby_table"] = table
            context["groupby_label"] = groupby_field.label
        return context


@register_model_view(models.ComplianceReport, "devices")
class ReportDeviceView(SingleTableMixin, FilterViewWithForm):
    table_class = tables.ComplianceReportDeviceTable
    tab = ViewTab(
        "Devices",
        badge=lambda obj: models.VDevice.objects.filter(results__in=obj.results.all())
        .order_by("pk")
        .distinct("pk")
        .count(),
    )
    filterset_class = filtersets.DeviceReportFilterSet
    permission_required = "view_compliancereport"
    template_name = "validity/report_devices.html"
    filterform_class = forms.DeviceReportFilterForm

    @functools.cached_property
    def object(self):
        return get_object_or_404(models.ComplianceReport, pk=self.kwargs["pk"])

    def get_queryset(self) -> QuerySet[models.VDevice]:
        severity_ge = SeverityChoices.from_request(self.request)
        return (
            models.VDevice.objects.filter(results__report=self.object)
            .annotate_result_stats(self.object.pk, severity_ge)
            .prefetch_results(self.object.pk, severity_ge)
        )

    def get_filterform_initial(self):
        return super().get_filterform_initial() | {"severity_ge": SeverityChoices.from_request(self.request)}

    def get_table(self, **kwargs):
        table_class = self.get_table_class()
        table = table_class(data=self.get_table_data(), **kwargs)
        table.configure(self.request)
        return table

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(**kwargs) | {
            "object": self.object,
            "tab": self.tab,
            "read_only": True,
            "search_button_name": _("Show"),
        }


@register_model_view(models.ComplianceReport, "results")
class ReportResultView(TestResultBaseView):
    parent_model = models.ComplianceReport
    result_relation = "report"
    read_only = True
    exclude_form_fields = ("latest", "selector_id", "platform_id", "tenant_id", "device_role_id", "manufacturer_id")
    permission_required = "view_compliancereport"


@register_model_view(models.ComplianceReport, "delete")
class ReportDeleteView(generic.ObjectDeleteView):
    queryset = models.ComplianceReport.objects.all()
