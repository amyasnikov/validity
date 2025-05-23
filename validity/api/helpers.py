from django.core.exceptions import ValidationError
from django.db.models import ManyToManyField
from rest_framework.permissions import BasePermission
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import HyperlinkedIdentityField, JSONField, ModelSerializer

from validity.fields.encrypted import EncryptedDict
from validity.utils.misc import partialcls


def proxy_factory(serializer_class: type[ModelSerializer], view_name: str) -> type[ModelSerializer]:
    """
    Creates Nested Serializer suitable for a proxy model.
    """
    url = HyperlinkedIdentityField(view_name=view_name)
    serializer_with_right_url = type(serializer_class.__name__, (serializer_class,), {"url": url})
    return partialcls(serializer_with_right_url, nested=True)


def model_perms(*permissions: str) -> type[BasePermission]:
    """
    Returns permission class suitable for a list of django model permissions
    """

    class Permission(BasePermission):
        def has_permission(self, request, view):
            return request.user.is_authenticated and request.user.has_perms(permissions)

    return Permission


class EncryptedDictField(JSONField):
    def __init__(self, **kwargs):
        self.do_not_encrypt = kwargs.pop("do_not_encrypt", ())
        super().__init__(**kwargs)

    def to_representation(self, value):
        if not isinstance(value, EncryptedDict):
            value = EncryptedDict(value, do_not_encrypt=self.do_not_encrypt)
        return value.encrypted

    def to_internal_value(self, data):
        return EncryptedDict(super().to_internal_value(data), do_not_encrypt=self.do_not_encrypt)


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

    def _validate(self, attrs):
        instance = self.instance or self.Meta.model()
        for field, field_value in attrs.items():
            if not isinstance(instance._meta.get_field(field), ManyToManyField):
                setattr(instance, field, field_value)
        if not instance.subform_type:
            return
        subform = instance.get_subform()
        if not subform.is_valid():
            errors = [
                ": ".join((field, err[0])) if field != "__all__" else err for field, err in subform.errors.items()
            ]
            raise ValidationError({instance.subform_json_field: errors})
        instance.subform_json = attrs[instance.subform_json_field] = subform.data_for_saving
        return attrs

    def validate(self, attrs):
        if isinstance(attrs, dict):
            attrs = self._validate(attrs)
        return attrs


class PrimaryKeyField(PrimaryKeyRelatedField):
    """
    Returns primary key only instead of the whole model instance
    """

    def to_internal_value(self, data):
        obj = super().to_internal_value(data)
        return obj.pk
