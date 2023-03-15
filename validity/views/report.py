from typing import Any, Iterable, Iterator

from netbox.views import generic
from utilities.views import register_model_view

from validity import forms, models, tables
from validity.choices import DeviceGroupByChoices
from .test_result import TestResultBaseView


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


@register_model_view(models.ComplianceReport, "results")
class ReportResultView(TestResultBaseView):
    parent_model = models.ComplianceReport
    result_relation = "report"
    read_only = True
    exclude_form_fields = ("latest", "selector_id", "platform_id", "tenant_id", "device_role_id", "manufacturer_id")
