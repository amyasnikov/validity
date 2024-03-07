import operator
from functools import cached_property, reduce
from typing import Generic, TypeVar, get_args

from django.db.models import Model, Q, QuerySet
from django.utils.functional import classproperty
from extras.models import Tag

from validity import models


class DBObject(int):
    def __new__(cls, value, model):
        return super().__new__(cls, value)

    def __init__(self, value, model):
        self.model = model
        super().__init__()

    @cached_property
    def obj(self):
        return self.model.objects.filter(pk=self).first()


class QuerySetObject(list):
    def __init__(self, iterable, model=None):
        self.model = model
        super().__init__(iterable)


class AllQuerySetObject(QuerySetObject):
    """
    Defaults to "all" if empty
    """

    @property
    def queryset(self):
        if not self:
            return self.model.objects.all()
        return self.model.objects.filter(pk__in=iter(self))


class EmptyQuerySetObject(QuerySetObject):
    """
    Defaults to "none" if empty
    """

    @property
    def queryset(self):
        if not self:
            return self.model.objects.none()
        return self.model.objects.filter(pk__in=iter(self))


class DBField:
    def __init__(self, model, object_cls, default=None) -> None:
        self.model = model
        self.object_cls = object_cls
        self.attr_name = None
        if default is not None and not isinstance(default, object_cls):
            default = object_cls(default, model)
        self.default = default

    def __set_name__(self, parent_cls, attr_name):
        self.attr_name = attr_name

    def __get__(self, instance, type_):
        return instance.__dict__.get(self.attr_name, self.default)

    def __set__(self, instance, value):
        if value is not None:
            value = self.object_cls(value, self.model)
        instance.__dict__[self.attr_name] = value


class ScriptData:
    def from_queryset(self, queryset: QuerySet) -> list[int]:
        """
        Extract primary keys from queryset
        """
        return list(queryset.values_list("pk", flat=True))

    def __init__(self, data) -> None:
        for k, v in data.items():
            if isinstance(v, QuerySet):
                v = self.from_queryset(v)
            elif isinstance(v, Model):
                v = v.pk
            setattr(self, k, v)


_ScriptData = TypeVar("_ScriptData", bound=ScriptData)


class ScriptDataMixin(Generic[_ScriptData]):
    """
    Mixin for Script. Allows to define script data cls in class definition and later use it.
    Example:
    self.script_data = self.script_data_cls(data)
    """

    script_data: _ScriptData

    @classproperty
    def script_data_cls(cls) -> type[_ScriptData]:
        for base_classes in cls.__orig_bases__:
            if (args := get_args(base_classes)) and issubclass(args[0], ScriptData):
                return args[0]
        raise AttributeError(f"No ScriptData definition found for {cls.__name__}")


class RunTestsScriptData(ScriptData):
    sync_datasources = False
    make_report = True
    selectors = DBField(models.ComplianceSelector, AllQuerySetObject, default=[])
    devices = DBField(models.VDevice, AllQuerySetObject, default=[])
    test_tags = DBField(Tag, EmptyQuerySetObject, default=[])
    explanation_verbosity = 2
    override_datasource = DBField(models.VDataSource, DBObject, default=None)

    @cached_property
    def device_filter(self) -> Q:
        filtr = Q()
        if self.selectors:
            filtr &= reduce(operator.or_, (qs.filter for qs in self.selectors.queryset))
        if self.devices:
            filtr &= reduce(operator.or_, (Q(pk=pk) for pk in self.devices))
        return filtr
