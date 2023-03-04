from itertools import chain
from typing import Sequence

from netbox.api.serializers import WritableNestedSerializer
from rest_framework.serializers import CharField, ModelSerializer


def nested_factory(
    serializer: type[ModelSerializer], meta_fields: Sequence[str], attributes: Sequence[str] = ("url",)
) -> type[ModelSerializer]:
    class Meta:
        model = serializer.Meta.model
        fields = meta_fields

    name = "Nested" + serializer.__name__
    mixins = (cls for cls in serializer.__bases__ if not issubclass(cls, ModelSerializer))
    bases = tuple(chain(mixins, (WritableNestedSerializer,)))
    s_attribs = {a: serializer._declared_fields[a] for a in attributes}
    s_attribs["Meta"] = Meta
    return type(
        name,
        bases,
        s_attribs,
    )


class PasswordField(CharField):
    def to_representation(self, value):
        return "$encrypted"
