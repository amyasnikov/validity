from dcim.filtersets import DeviceFilterSet
from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables
from .base import TableMixin


class GitRepoListView(generic.ObjectListView):
    queryset = models.GitRepo.objects.all()
    table = tables.GitRepoTable
    filterset = filtersets.GitRepoFilterSet
    filterset_form = forms.GitRepoFilterForm


@register_model_view(models.GitRepo)
class GitRepoView(TableMixin, generic.ObjectView):
    queryset = models.GitRepo.objects.prefetch_related("tags")
    table = DeviceTable
    filterset = DeviceFilterSet
    object_table_field = "bound_devices"


@register_model_view(models.GitRepo, "delete")
class GitRepoDeleteView(generic.ObjectDeleteView):
    queryset = models.GitRepo.objects.all()


class GitRepoBulkDeleteView(generic.BulkDeleteView):
    queryset = models.GitRepo.objects.all()
    filterset = filtersets.GitRepoFilterSet
    table = tables.GitRepoTable


@register_model_view(models.GitRepo, "edit")
class GitRepoEditView(generic.ObjectEditView):
    queryset = models.GitRepo.objects.all()
    form = forms.GitRepoForm
