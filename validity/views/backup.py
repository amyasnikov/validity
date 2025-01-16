from typing import Annotated

from netbox.views import generic
from utilities.views import register_model_view

from validity import di, filtersets, forms, models, tables
from validity.scripts import BackUpParams, Launcher
from .base import LauncherMixin


class BackupPointListView(generic.ObjectListView):
    queryset = models.BackupPoint.objects.select_related("data_source")
    table = tables.BackupPointTable
    filterset = filtersets.BackupPointFilterSet
    filterset_form = forms.BackupPointFilterForm


@register_model_view(models.BackupPoint)
class BackupPointView(LauncherMixin, generic.ObjectView):
    queryset = models.BackupPoint.objects.all()

    @di.inject
    def __init__(self, launcher: Annotated[Launcher, "backup_launcher"], **kwargs):
        self.launcher = launcher
        super().__init__(**kwargs)

    def get_required_permission(self):
        if self.request.GET:
            return super().get_required_permission()
        return "validity.backup_backuppoint"

    def post(self, request, **kwargs):
        params = BackUpParams(backuppoint_id=kwargs["pk"], request=request)
        return self.launch_or_render_error(params, **kwargs)


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
