from django.db.models import TextChoices
from django.db.models.enums import ChoicesMeta
from django.utils.translation import gettext_lazy as _


class ColoredChoiceMeta(ChoicesMeta):
    """
    Allows to write choice fields with a color like that:
        option1 = 'red'
        option2 = ('option2', 'yellow')
        option3 = ('option3', 'Option3', 'green')
    """

    def __new__(cls, name, bases, namespace, **kwargs):
        colors = {}
        member_names = namespace._member_names
        namespace._member_names = []
        for key in member_names:
            attr = namespace.pop(key)
            if isinstance(attr, str):
                colors[key] = attr
                attr = key
            elif isinstance(attr, (list, tuple)):
                colors[key] = attr[-1]
                attr = attr[:-1]
            namespace[key] = attr
        namespace["_colors"] = colors
        namespace._member_names.remove("_colors")
        return super().__new__(cls, name, bases, namespace, **kwargs)

    @property
    def colors(self):
        return self._colors


class BoolOperationChoices(TextChoices, metaclass=ColoredChoiceMeta):
    OR = "OR", _("OR"), "purple"
    AND = "AND", _("AND"), "blue"


class DynamicPairsChoices(TextChoices, metaclass=ColoredChoiceMeta):
    NO = "NO", _("NO"), "red"
    NAME = "NAME", _("By name regex group"), "blue"


class SeverityChoices(TextChoices, metaclass=ColoredChoiceMeta):
    LOW = "LOW", _("LOW"), "green"
    MIDDLE = "MIDDLE", _("MIDDLE"), "yellow"
    HIGH = "HIGH", _("HIGH"), "red"


class ConfigExtractionChoices(TextChoices, metaclass=ColoredChoiceMeta):
    TTP = "TTP", "TTP", "purple"
    JSON = "JSON", "JSON", "orange"
    YAML = "YAML", "YAML", "info"
