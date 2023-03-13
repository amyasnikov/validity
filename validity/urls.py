from django.urls import include, path
from utilities.urls import get_model_urls

from . import views


urlpatterns = [
    path("git-repositories/", views.GitRepoListView.as_view(), name="gitrepo_list"),
    path("git-repositories/add/", views.GitRepoEditView.as_view(), name="gitrepo_add"),
    path("git-repositories/delete/", views.GitRepoBulkDeleteView.as_view(), name="gitrepo_bulk_delete"),
    path("git-repositories/<int:pk>/", include(get_model_urls("validity", "gitrepo"))),
    path("selectors/", views.ComplianceSelectorListView.as_view(), name="complianceselector_list"),
    path("selectors/add/", views.ComplianceSelectorEditView.as_view(), name="complianceselector_add"),
    path("selectors/delete/", views.ComplianceSelectorBulkDeleteView.as_view(), name="complianceselector_bulk_delete"),
    path("selectors/<int:pk>/", include(get_model_urls("validity", "complianceselector"))),
    path("tests/", views.ComplianceTestListView.as_view(), name="compliancetest_list"),
    path("tests/add/", views.ComplianceTestEditView.as_view(), name="compliancetest_add"),
    path("tests/delete/", views.ComplianceTestBulkDeleteView.as_view(), name="compliancetest_bulk_delete"),
    path("tests/<int:pk>/", include(get_model_urls("validity", "compliancetest"))),
    path("test-results/", views.ComplianceResultListView.as_view(), name="compliancetestresult_list"),
    path("test-results/<int:pk>/", include(get_model_urls("validity", "compliancetestresult"))),
    path("serializers/", views.ConfigSerializerListView.as_view(), name="configserializer_list"),
    path("serializers/add/", views.ConfigSerializerEditView.as_view(), name="configserializer_add"),
    path("serializers/delete/", views.ConfigSerializerBulkDeleteView.as_view(), name="configserializer_bulk_delete"),
    path("serializers/<int:pk>/", include(get_model_urls("validity", "configserializer"))),
    path("namesets/", views.NameSetListView.as_view(), name="nameset_list"),
    path("namesets/add/", views.NameSetEditView.as_view(), name="nameset_add"),
    path("namesets/delete/", views.NameSetBulkDeleteView.as_view(), name="nameset_bulk_delete"),
    path("namesets/<int:pk>/", include(get_model_urls("validity", "nameset"))),
    path("reports/", views.ComplianceReportListView.as_view(), name="compliancereport_list"),
    path("reports/<int:pk>/", include(get_model_urls("validity", "compliancereport"))),
]
