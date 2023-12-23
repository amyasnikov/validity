import yaml
from django.utils.translation import gettext_lazy as _
from extras.plugins import PluginTemplateExtension

from validity.pollers.result import PollingInfo


class DataSourceExtension(PluginTemplateExtension):
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


template_extensions = [DataSourceExtension]
