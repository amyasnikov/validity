# NetBox 4.0
from pydoc import locate as __locate

from .old import *


FieldSet = __locate("utilities.forms.rendering.FieldSet")
plugins = __locate("netbox.plugins")
ButtonColorChoices = __locate("netbox.choices.ButtonColorChoices")
PluginTemplateExtension = __locate("netbox.plugins.PluginTemplateExtension")
CF_OBJ_TYPE = "related_object_type"
CF_CONTENT_TYPES = "object_types"


class BootstrapMixin:
    pass
