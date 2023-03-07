from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from validity import filtersets, forms, models, tables


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


@register_model_view(models.ComplianceTest, "test_results", "results")
class TestResultView(SingleTableMixin, FilterView):
    template_name = "validity/compliance_results.html"
    tab = ViewTab("Results")
    model = models.ComplianceTestResult
    filterset_class = filtersets.ComplianceTestResultFilterSet
    filter_form_class = forms.TestResultFilterForm
    table_class = tables.ComplianceResultTable

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.exclude = ("test",)
        return table

    def get_queryset(self):
        return models.ComplianceTestResult.objects.select_related("test", "device").filter(test=self.kwargs["pk"])

    def get_object(self):
        return get_object_or_404(models.ComplianceTest, pk=self.kwargs["pk"])

    def get_filterform_initial(self):
        if not hasattr(self.filterset.form, "cleaned_data"):
            return {}
        return {k: v for k, v in self.filterset.form.cleaned_data.items() if k in self.filter_form_class.base_fields}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset_form"] = self.filter_form_class(initial=self.get_filterform_initial())
        context["object"] = self.get_object()
        context["tab"] = self.tab
        return context


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
