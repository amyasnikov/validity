from django.urls import include, path
from utilities.urls import get_model_urls

from . import views


urlpatterns = [
    path("selectors/", views.ComplianceSelectorListView.as_view(), name="complianceselector_list"),
    path("selectors/add/", views.ComplianceSelectorEditView.as_view(), name="complianceselector_add"),
    path("selectors/delete/", views.ComplianceSelectorBulkDeleteView.as_view(), name="complianceselector_bulk_delete"),
    path("selectors/import/", views.ComplianceSelectorBulkImportView.as_view(), name="complianceselector_import"),
    path("selectors/<int:pk>/", include(get_model_urls("validity", "complianceselector"))),
    path("tests/", views.ComplianceTestListView.as_view(), name="compliancetest_list"),
    path("tests/run/", views.RunTestsView.as_view(), name="compliancetest_run"),
    path("tests/add/", views.ComplianceTestEditView.as_view(), name="compliancetest_add"),
    path("tests/delete/", views.ComplianceTestBulkDeleteView.as_view(), name="compliancetest_bulk_delete"),
    path("tests/import/", views.ComplianceTestBulkImportView.as_view(), name="compliancetest_import"),
    path("tests/<int:pk>/", include(get_model_urls("validity", "compliancetest"))),
    path("test-results/", views.ComplianceResultListView.as_view(), name="compliancetestresult_list"),
    path("test-results/<int:pk>/", include(get_model_urls("validity", "compliancetestresult"))),
    path("serializers/", views.SerializerListView.as_view(), name="serializer_list"),
    path("serializers/add/", views.SerializerEditView.as_view(), name="serializer_add"),
    path("serializers/delete/", views.SerializerBulkDeleteView.as_view(), name="serializer_bulk_delete"),
    path("serializers/import/", views.SerializerBulkImportView.as_view(), name="serializer_import"),
    path("serializers/<int:pk>/", include(get_model_urls("validity", "serializer"))),
    path("namesets/", views.NameSetListView.as_view(), name="nameset_list"),
    path("namesets/add/", views.NameSetEditView.as_view(), name="nameset_add"),
    path("namesets/delete/", views.NameSetBulkDeleteView.as_view(), name="nameset_bulk_delete"),
    path("namesets/import/", views.NameSetBulkImportView.as_view(), name="nameset_import"),
    path("namesets/<int:pk>/", include(get_model_urls("validity", "nameset"))),
    path("reports/", views.ComplianceReportListView.as_view(), name="compliancereport_list"),
    path("reports/<int:pk>/", include(get_model_urls("validity", "compliancereport"))),
    # hack to display NetBox Job view without an error
    path("reports/<int:pk>/", views.ComplianceReportView.as_view(), name="compliancereport_jobs"),
    path("pollers/", views.PollerListView.as_view(), name="poller_list"),
    path("pollers/add/", views.PollerEditView.as_view(), name="poller_add"),
    path("pollers/delete/", views.PollerBulkDeleteView.as_view(), name="poller_bulk_delete"),
    path("pollers/import/", views.PollerBulkImportView.as_view(), name="poller_import"),
    path("pollers/<int:pk>/", include(get_model_urls("validity", "poller"))),
    path("commands/", views.CommandListView.as_view(), name="command_list"),
    path("commands/add/", views.CommandEditView.as_view(), name="command_add"),
    path("commands/delete/", views.CommandBulkDeleteView.as_view(), name="command_bulk_delete"),
    path("commands/import/", views.CommandBulkImportView.as_view(), name="command_import"),
    path("commands/<int:pk>/", include(get_model_urls("validity", "command"))),
    path("scripts/results/<int:pk>/", views.ScriptResultView.as_view(), name="script_result"),
]
