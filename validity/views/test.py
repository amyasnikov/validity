from django.db.models import Count, Q
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from .test_result import TestResultBaseView


class ComplianceTestListView(generic.ObjectListView):
    queryset = models.ComplianceTest.objects.annotate_latest_count()
    table = tables.ComplianceTestTable
    filterset = filtersets.ComplianceTestFilterSet
    filterset_form = forms.ComplianceTestFilterForm


@register_model_view(models.ComplianceTest)
class ComplianceTestView(generic.ObjectView):
    queryset = models.ComplianceTest.objects.prefetch_related("namesets")

    def get_extra_context(self, request, instance):
        global_namesets = models.NameSet.objects.filter(_global=True)
        table = tables.NameSetTable(instance.namesets.all() | global_namesets)
        table.configure(request)
        return {"nameset_table": table}


@register_model_view(models.ComplianceTest, "results")
class TestResultView(TestResultBaseView):
    parent_model = models.ComplianceTest
    result_relation = "test"
    exclude_form_fields = ("platform_id", "tenant_id", "device_role_id", "manufacturer_id", "report_id", "selector_id")


@register_model_view(models.ComplianceTest, "delete")
class ComplianceTestDeleteView(generic.ObjectDeleteView):
    queryset = models.ComplianceTest.objects.all()


class ComplianceTestBulkDeleteView(generic.BulkDeleteView):
    queryset = models.ComplianceTest.objects.pf_latest_results().annotate(
        passed=Count("results", filter=Q(results__passed=True)),
        failed=Count("results", filter=Q(results__passed=False)),
    )
    filterset = filtersets.ComplianceTestFilterSet
    table = tables.ComplianceTestTable


@register_model_view(models.ComplianceTest, "edit")
class ComplianceTestEditView(generic.ObjectEditView):
    queryset = models.ComplianceTest.objects.all()
    form = forms.ComplianceTestForm
