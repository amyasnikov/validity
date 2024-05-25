from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from netbox.views import generic
from utilities.views import register_model_view

from validity import config, filtersets, forms, models, tables
from .base import TableMixin, TestResultBaseView


class ComplianceTestListView(generic.ObjectListView):
    queryset = models.ComplianceTest.objects.annotate_latest_count()
    table = tables.ComplianceTestTable
    filterset = filtersets.ComplianceTestFilterSet
    filterset_form = forms.ComplianceTestFilterForm


@register_model_view(models.ComplianceTest)
class ComplianceTestView(TableMixin, generic.ObjectView):
    queryset = models.ComplianceTest.objects.prefetch_related("namesets")
    table = tables.NameSetTable
    filterset = filtersets.NameSetFilterSet

    def get_table_qs(self, request, instance):
        return models.NameSet.objects.filter(Q(_global=True) | Q(tests__pk=instance.pk))


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


def run_tests(request):
    if config.netbox_version < "4.0.0":
        return redirect("extras:script", module="validity_scripts", name="RunTests")
    from extras.models import Script

    script = get_object_or_404(Script, name="RunTests", module__data_file__path="validity_scripts.py")
    return redirect("extras:script", pk=script.pk)
