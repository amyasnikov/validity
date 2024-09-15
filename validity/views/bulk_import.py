from netbox.views.generic.bulk_views import BulkImportView

from validity import forms, models


class ComplianceTestBulkImportView(BulkImportView):
    queryset = models.ComplianceTest.objects.all()
    model_form = forms.ComplianceTestImportForm


class NameSetBulkImportView(BulkImportView):
    queryset = models.NameSet.objects.all()
    model_form = forms.NameSetImportForm

    def post(self, request):
        return super().post(request)


class SerializerBulkImportView(BulkImportView):
    queryset = models.Serializer.objects.all()
    model_form = forms.SerializerImportForm


class ComplianceSelectorBulkImportView(BulkImportView):
    queryset = models.ComplianceSelector.objects.all()
    model_form = forms.ComplianceSelectorImportForm


class CommandBulkImportView(BulkImportView):
    queryset = models.Command.objects.all()
    model_form = forms.CommandImportForm


class PollerBulkImportView(BulkImportView):
    queryset = models.Poller.objects.all()
    model_form = forms.PollerImportForm
