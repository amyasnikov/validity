from netbox.api.routers import NetBoxRouter

from . import views


router = NetBoxRouter()

router.register("selectors", views.ComplianceSelectorViewSet)
router.register("tests", views.ComplianceTestViewSet)
router.register("test-results", views.ComplianceTestResultViewSet)
router.register("git-repositories", views.GitRepoViewSet)
router.register('serializers', views.ConfigSerializerViewSet)

urlpatterns = router.urls

app_name = "validity"
