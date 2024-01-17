import pytest
from dcim.models import Device
from django.db import connection
from django.db.models import BigIntegerField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from factories import DeviceFactory, NameSetDBFactory, SerializerDBFactory

from validity.models import NameSet
from validity.models.serializer import Serializer
from validity.utils.orm import CustomPrefetchMixin, QuerySetMap


@pytest.mark.parametrize("attrib", ["pk", "name"])
@pytest.mark.django_db
def test_qsmap(attrib):
    devices = [DeviceFactory(), DeviceFactory(), DeviceFactory()]
    qs_map = QuerySetMap(Device.objects.all(), attrib)
    assert len(connection.queries) == 0
    for device in devices:
        key = getattr(device, attrib)
        assert key in qs_map
        assert qs_map[key] == device


@pytest.mark.django_db
def test_custom_prefetch():
    devices = [DeviceFactory(), DeviceFactory(), DeviceFactory()]
    device_qs = Device.objects.all()
    custom_qs = CustomPrefetchMixin(device_qs.model, device_qs._query, device_qs._db, device_qs._hints)
    serializers = [SerializerDBFactory(), SerializerDBFactory(), SerializerDBFactory()]
    device_serializer_map = {}
    for d, s in zip(devices, serializers):
        d.custom_field_data["serializer"] = s.pk
        d.save()
        device_serializer_map[d.pk] = s.pk

    for device in custom_qs.annotate(
        serializer_id=Cast(KeyTextTransform("serializer", "custom_field_data"), BigIntegerField())
    ).custom_prefetch("serializer", Serializer.objects.all()):
        assert device_serializer_map[device.pk] == device.serializer.pk


@pytest.mark.django_db
def test_custom_postfetch(monkeypatch):
    DeviceFactory(name="dev0")
    DeviceFactory(name="dev1")
    DeviceFactory(name="dev2")
    device_qs = Device.objects.all()
    monkeypatch.setattr(Device, "ns", property(lambda self: "ns" + self.name[-1]), raising=False)
    custom_qs = CustomPrefetchMixin(
        device_qs.model, device_qs._query, device_qs._db, device_qs._hints
    ).custom_postfetch("nameset", NameSet.objects.all(), pk_field="ns", remote_pk_field="name")
    for i in range(4):
        NameSetDBFactory(name=f"ns{i}")
    for device in custom_qs:
        assert device.name.replace("dev", "ns") == device.nameset.name
