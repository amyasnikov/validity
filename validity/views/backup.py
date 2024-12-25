from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables


class BackupPointListView(generic.ObjectListView):
    queryset = models.BackupPoint.objects.select_related("data_source")
    table = tables.BackupPointTable
    filterset = filtersets.BackupPointFilterSet
    filterset_form = forms.BackupPointFilterForm


@register_model_view(models.BackupPoint)
class BackupPointView(generic.ObjectView):
    queryset = models.BackupPoint.objects.all()


@register_model_view(models.BackupPoint, "delete")
class BackupPointDeleteView(generic.ObjectDeleteView):
    queryset = models.BackupPoint.objects.all()


class BackupPointBulkDeleteView(generic.BulkDeleteView):
    queryset = models.BackupPoint.objects.select_related("data_source")
    filterset = filtersets.BackupPointFilterSet
    table = tables.BackupPointTable


@register_model_view(models.BackupPoint, "edit")
class BackupPointEditView(generic.ObjectEditView):
    queryset = models.BackupPoint.objects.all()
    form = forms.BackupPointForm
