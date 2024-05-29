# NetBox 3.6
from pydoc import locate as __locate


enqueue_object = __locate("extras.webhooks.enqueue_object")
events_queue = __locate("netbox.context.webhooks_queue")
EventRulesMixin = __locate("netbox.models.features.WebhooksMixin")
BootstrapMixin = __locate("utilities.forms.BootstrapMixin")
plugins = __locate("extras.plugins")
ButtonColorChoices = __locate("utilities.choices.ButtonColorChoices")
PluginTemplateExtension = __locate("extras.plugins.PluginTemplateExtension")


class FieldSet:
    def __new__(cls, *items, name):
        return name, items


CF_OBJ_TYPE = "object_type"
CF_CONTENT_TYPES = "content_types"
