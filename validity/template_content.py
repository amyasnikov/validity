import yaml
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from tenancy.models import Tenant

from validity.netbox_changes import PluginTemplateExtension
from validity.pollers.result import PollingInfo


class PollingInfoExtension(PluginTemplateExtension):
    model = "core.datasource"

    def get_polling_info(self, data_file) -> str:
        if not data_file:
            return _("No polling info yet.")
        polling_info = PollingInfo.model_validate(yaml.safe_load(data_file.data_as_string))
        return yaml.safe_dump(polling_info.model_dump(exclude={"errors"}))

    def right_page(self):
        if self.context["object"].type != "device_polling":
            return ""
        polling_info_file = self.context["object"].datafiles.filter(path="polling_info.yaml").first()
        text = self.get_polling_info(polling_info_file)
        return self.render(
            "validity/inc/yaml_card.html",
            extra_context={
                "content": text,
                "title_link": polling_info_file.get_absolute_url() if polling_info_file else "",
                "title": _("Polling info"),
            },
        )


class DataSourceTenantExtension(PluginTemplateExtension):
    model = "core.datasource"

    def right_page(self):
        instance = self.context["object"]
        tenant_qs = Tenant.objects.restrict(self.context["request"].user, "view").filter(
            custom_field_data__data_source=instance.pk
        )
        if not (qs_count := tenant_qs.count()):
            return ""
        related_models = [(qs_count, tenant_qs.model, "cf_data_source")]
        return self.render(
            "validity/inc/related_objects.html",
            extra_context={"related_models": related_models},
        )


class ComplianceTestExtension(PluginTemplateExtension):
    model = "validity.compliancetest"

    def list_buttons(self):
        run_tests_url = reverse("plugins:validity:compliancetest_run")
        icon = '<i class="mdi mdi-rocket-launch"></i>'
        return f'<a class="btn btn-pink" href="{run_tests_url}">{icon} Run Tests</a>'


template_extensions = [DataSourceTenantExtension, PollingInfoExtension, ComplianceTestExtension]
