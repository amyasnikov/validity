from netbox.views import generic
from utilities.views import register_model_view

from validity import filtersets, forms, models, tables


class NameSetListView(generic.ObjectListView):
    queryset = models.NameSet.objects.prefetch_related("tests")
    table = tables.NameSetTable
    filterset = filtersets.NameSetFilterSet
    filterset_form = forms.NameSetFilterForm


@register_model_view(models.NameSet)
class NameSetView(generic.ObjectView):
    queryset = models.NameSet.objects.prefetch_related("tests", "tags")

    def get_extra_context(self, request, instance):
        return {"global": instance._global}


@register_model_view(models.NameSet, "delete")
class NameSetDeleteView(generic.ObjectDeleteView):
    queryset = models.NameSet.objects.all()


class NameSetBulkDeleteView(generic.BulkDeleteView):
    queryset = models.NameSet.objects.prefetch_related("tests")
    filterset = filtersets.NameSetFilterSet
    table = tables.NameSetTable


@register_model_view(models.NameSet, "edit")
class NameSetEditView(generic.ObjectEditView):
    queryset = models.NameSet.objects.all()
    form = forms.NameSetForm
