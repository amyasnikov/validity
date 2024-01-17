from dcim.api.urls import urlpatterns as dcim_urls
from django.urls import path
from netbox.api.routers import NetBoxRouter

from . import views


router = NetBoxRouter()

router.register("selectors", views.ComplianceSelectorViewSet)
router.register("tests", views.ComplianceTestViewSet)
router.register("test-results", views.ComplianceTestResultViewSet)
router.register("serializers", views.SerializerViewSet)
router.register("namesets", views.NameSetViewSet)
router.register("reports", views.ComplianceReportViewSet)
router.register("pollers", views.PollerViewSet)
router.register("commands", views.CommandViewSet)


urlpatterns = [
    path("reports/<int:pk>/devices/", views.DeviceReportView.as_view(), name="report_devices"),
] + router.urls


dcim_urls.append(
    path("devices/<int:pk>/serialized_state/", views.SerializedStateView.as_view(), name="serialized_state")
)


app_name = "validity"
