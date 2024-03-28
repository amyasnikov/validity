from itertools import chain
from typing import Sequence

from django.core.exceptions import ValidationError
from django.db.models import ManyToManyField
from netbox.api.serializers import WritableNestedSerializer
from rest_framework.serializers import JSONField, ModelSerializer

from validity.fields.encrypted import EncryptedDict


def nested_factory(
    serializer: type[ModelSerializer], meta_fields: Sequence[str], attributes: Sequence[str] = ("url",)
) -> type[ModelSerializer]:
    """
    Creates nested Serializer from regular one
    """

    class Meta:
        model = serializer.Meta.model
        fields = meta_fields

    name = "Nested" + serializer.__name__
    mixins = (cls for cls in serializer.__bases__ if not issubclass(cls, ModelSerializer))
    bases = tuple(chain(mixins, (WritableNestedSerializer,)))
    s_attribs = {a: serializer._declared_fields[a] for a in attributes}
    s_attribs["Meta"] = Meta
    return type(name, bases, s_attribs)


class EncryptedDictField(JSONField):
    def to_representation(self, value):
        return value.encrypted

    def to_internal_value(self, data):
        return EncryptedDict(super().to_internal_value(data))


class ListQPMixin:
    """
    Serializer Mixin. Allows to get list query params in 2 forms:
    1. ?param=v1&param=v2
    2. ?param=v1,v2
    """

    def get_list_param(self, param: str) -> list[str] | None:
        if "request" not in self.context or param not in self.context["request"].query_params:
            return None
        param_value = self.context["request"].query_params.getlist(param)
        if len(param_value) == 1:
            return param_value[0].split(",")
        return param_value


class FieldsMixin(ListQPMixin):
    """
    Serializer Mixin. Allows to include specific fields only
    """

    query_param = "fields"

    def to_representation(self, instance):
        if query_fields := self.get_list_param(self.query_param):
            self.fields = {
                field_name: field for field_name, field in self.fields.items() if field_name in set(query_fields)
            }
        return super().to_representation(instance)


class SubformValidationMixin:
    """
    Serializer Mixin. Validates JSON field according to a subform
    """

    def validate(self, attrs):
        if isinstance(attrs, dict):
            instance = self.instance or self.Meta.model()
            for field, field_value in attrs.items():
                if not isinstance(instance._meta.get_field(field), ManyToManyField):
                    setattr(instance, field, field_value)
            subform = instance.subform_cls(instance.subform_json)
            if not subform.is_valid():
                errors = [
                    ": ".join((field, err[0])) if field != "__all__" else err for field, err in subform.errors.items()
                ]
                raise ValidationError({instance.subform_json_field: errors})
        return attrs
