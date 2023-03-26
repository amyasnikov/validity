from collections import namedtuple
from typing import Callable

from django.db.models import Model
from django.shortcuts import get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from validity import filtersets, forms, models, tables
from validity.config_compliance.eval import repr_


class ComplianceResultListView(generic.ObjectListView):
    queryset = models.ComplianceTestResult.objects.select_related("test", "device")
    table = tables.ComplianceResultTable
    filterset = filtersets.ComplianceTestResultFilterSet
    filterset_form = forms.ComplianceTestResultFilterForm


@register_model_view(models.ComplianceTestResult)
class ComplianceResultView(generic.ObjectView):
    queryset = models.ComplianceTestResult.objects.select_related("test", "device")

    def get_result_table(self, request, instance):
        table = tables.ComplianceResultTable(
            models.ComplianceTestResult.objects.filter(test=instance.test, device=instance.device).exclude(
                pk=instance.pk
            )
        )
        table.exclude += ("test", "device")
        table.order_by = "last_updated"
        table.configure(request)
        return table

    @staticmethod
    def repr_func(verbose: bool) -> Callable:
        func = repr if verbose else repr_
        return lambda item: item if isinstance(item, str) else func(item)

    def get_explanation_table(self, request, instance):
        verbose = request.GET.get("verbose", "") == "true"
        repr_func = self.repr_func(verbose)
        Explanation = namedtuple("Explanation", "left right")
        explanations = (Explanation(*map(repr_func, item)) for item in instance.explanation)
        return tables.ExplanationTable(explanations)

    def get_extra_context(self, request, instance):
        result_table = self.get_result_table(request, instance)
        explanation_table = self.get_explanation_table(request, instance)
        return {"result_table": result_table, "explanation_table": explanation_table}


class TestResultBaseView(SingleTableMixin, FilterView):
    template_name = "validity/compliance_results.html"
    tab = ViewTab("Test Results", badge=lambda obj: obj.results.count())
    model = models.ComplianceTestResult
    filterset_class = filtersets.ComplianceTestResultFilterSet
    filter_form_class = forms.TestResultFilterForm
    table_class = tables.ComplianceResultTable

    parent_model: type[Model]
    result_relation: str
    read_only: bool = False
    exclude_form_fields: tuple[str, ...] = ()

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.exclude = (self.result_relation,)
        return table

    def get_queryset(self):
        return models.ComplianceTestResult.objects.select_related("test", "device").filter(
            **{self.result_relation: self.kwargs["pk"]}
        )

    def get_object(self):
        return get_object_or_404(self.parent_model, pk=self.kwargs["pk"])

    def get_filterform(self):
        if not hasattr(self.filterset.form, "cleaned_data"):
            initial = {}
        else:
            initial = {
                k: v for k, v in self.filterset.form.cleaned_data.items() if k in self.filter_form_class.base_fields
            }
        form = self.filter_form_class(
            initial=initial, exclude=self.exclude_form_fields + (self.result_relation + "_id",)
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context | {
            "filterset_form": self.get_filterform(),
            "object": self.get_object(),
            "tab": self.tab,
            "read_only": self.read_only,
            "result_relation": self.result_relation,
        }
