from collections import namedtuple
from typing import Callable

from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from validity.compliance.eval import repr_


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
