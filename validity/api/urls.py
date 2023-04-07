from dcim.api.urls import urlpatterns as dcim_urls
from django.urls import path
from netbox.api.routers import NetBoxRouter

from . import views


router = NetBoxRouter()

router.register("selectors", views.ComplianceSelectorViewSet)
router.register("tests", views.ComplianceTestViewSet)
router.register("test-results", views.ComplianceTestResultViewSet)
router.register("git-repositories", views.GitRepoViewSet)
router.register("serializers", views.ConfigSerializerViewSet)
router.register("namesets", views.NameSetViewSet)
router.register("reports", views.ComplianceReportViewSet)

urlpatterns = router.urls

app_name = "validity"


dcim_urls.append(
    path("devices/<int:pk>/serialized_config/", views.SerializedConfigView.as_view(), name="serialized_config")
)
