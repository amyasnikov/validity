from dcim.models import Device
from dcim.tables import DeviceTable
from django.db.models import Case, Q, When, Count, OuterRef, BigIntegerField
from netbox.views import generic
from utilities.views import register_model_view
from django.db.models.functions import Cast
from validity import filtersets, forms, models, tables


total_devices = Case(
    When(default=True, then=Count(Device.objects.filter(~Q(custom_field_data__has_key="git_repo")).values('id'))),
    default=Count(Device.objects.annotate(git_repo=Cast('custom_field_data__git_repo', BigIntegerField())).filter(git_repo=OuterRef("id")).values('id')),
)


class GitRepoListView(generic.ObjectListView):
    queryset = models.GitRepo.objects.annotate(total_devices=total_devices)
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
    queryset = models.GitRepo.objects.annotate(total_devices=total_devices)
    filterset = filtersets.GitRepoFilterSet
    table = tables.GitRepoTable


@register_model_view(models.GitRepo, "edit")
class GitRepoEditView(generic.ObjectEditView):
    queryset = models.GitRepo.objects.all()
    form = forms.GitRepoForm
