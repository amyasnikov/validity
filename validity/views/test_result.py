from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, models, tables


class ComplianceResultListView(generic.ObjectListView):
    queryset = models.ComplianceTestResult.objects.select_related("test", "device")
    table = tables.ComplianceResultTable
    filterset = filtersets.ComplianceTestResultFilterSet


@register_model_view(models.ComplianceTestResult)
class ComplianceResultView(generic.ObjectView):
    queryset = models.ComplianceTestResult.objects.select_related("test", "device")

    def get_extra_context(self, request, instance):
        table = tables.ComplianceResultTable(
            models.ComplianceTestResult.objects.filter(test=instance.test, device=instance.device).exclude(
                pk=instance.pk
            )
        )
        table.exclude += ("test", "device")
        table.order_by = "last_updated"
        table.configure(request)
        return {"result_table": table}
