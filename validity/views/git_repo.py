from dcim.models import Device
from dcim.tables import DeviceTable
from netbox.views import generic
from utilities.views import register_model_view
from validity import filtersets, forms, models, tables


class GitRepoListView(generic.ObjectListView):
    queryset = models.GitRepo.objects.annotate_total_devices()
    table = tables.GitRepoTable
    filterset = filtersets.GitRepoFilterSet


@register_model_view(models.GitRepo)
class GitRepoView(generic.ObjectView):
    queryset = models.GitRepo.objects.all()

    def get_extra_context(self, request, instance):
        table = DeviceTable(Device.objects.filter(custom_field_data__git_repo=instance.pk))
        table.configure(request)
        return {"device_table": table}


@register_model_view(models.GitRepo, "delete")
class GitRepoDeleteView(generic.ObjectDeleteView):
    queryset = models.GitRepo.objects.all()


class GitRepoBulkDeleteView(generic.BulkDeleteView):
    queryset = models.GitRepo.objects.annotate_total_devices()
    filterset = filtersets.GitRepoFilterSet
    table = tables.GitRepoTable


@register_model_view(models.GitRepo, "edit")
class GitRepoEditView(generic.ObjectEditView):
    queryset = models.GitRepo.objects.all()
    form = forms.GitRepoForm
