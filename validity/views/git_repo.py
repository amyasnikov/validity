from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables


class GitRepoListView(generic.ObjectListView):
    queryset = models.GitRepo.objects.all()
    table = tables.GitRepoTable
    filterset = filtersets.GitRepoFilterSet
    filterset_form = forms.GitRepoFilterForm


@register_model_view(models.GitRepo)
class GitRepoView(generic.ObjectView):
    queryset = models.GitRepo.objects.prefetch_related("tags")

    def get_extra_context(self, request, instance):
        table = DeviceTable(instance.bound_devices())
        table.configure(request)
        return {"device_table": table}


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
