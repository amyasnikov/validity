# NetBox 3.7
from pydoc import locate as __locate


BootstrapMixin = __locate("utilities.forms.BootstrapMixin")
plugins = __locate("extras.plugins")
ButtonColorChoices = __locate("utilities.choices.ButtonColorChoices")
PluginTemplateExtension = __locate("extras.plugins.PluginTemplateExtension")
htmx_partial = __locate("utilities.htmx.is_htmx")
enqueue_event = __locate("extras.events.enqueue_object")
NestedTenantSerializer = __locate("tenancy.")


class FieldSet:
    def __new__(cls, *items, name):
        return name, items


CF_OBJ_TYPE = "object_type"
CF_CONTENT_TYPES = "content_types"
QUEUE_CREATE_ACTION = "create"
