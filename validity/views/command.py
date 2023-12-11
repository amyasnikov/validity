from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables


class CommandListView(generic.ObjectListView):
    queryset = models.Command.objects.all()
    table = tables.CommandTable
    filterset = filtersets.CommandFilterSet
    filterset_form = forms.CommandFilterForm


@register_model_view(models.Command)
class CommandView(generic.ObjectView):
    queryset = models.Command.objects.all()

    def get_extra_context(self, request, instance):
        return super().get_extra_context(request, instance) | {"format": request.GET.get("format", "yaml")}


@register_model_view(models.Command, "delete")
class CommandDeleteView(generic.ObjectDeleteView):
    queryset = models.Command.objects.all()


class CommandBulkDeleteView(generic.BulkDeleteView):
    queryset = models.Command.objects.all()
    filterset = filtersets.CommandFilterSet
    table = tables.CommandTable


@register_model_view(models.Command, "edit")
class CommandEditView(generic.ObjectEditView):
    queryset = models.Command.objects.all()
    form = forms.CommandForm
