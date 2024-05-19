from operator import attrgetter

import pytest
from dcim.models import Device
from factories import (
    DataFileFactory,
    DataSourceFactory,
    DeviceFactory,
    SelectorFactory,
    SerializerDBFactory,
    TenantFactory,
)
from ipam.models import IPAddress

from validity.compliance.serialization import Serializable
from validity.models import VDevice


@pytest.fixture
def setup_serializers(create_custom_fields):
    serializers = [SerializerDBFactory() for _ in range(3)]
    devices = [DeviceFactory() for _ in range(3)]
    attrs = ["custom_field_data", "device_type.custom_field_data", "device_type.manufacturer.custom_field_data"]
    for device, serializer, attr in zip(devices, serializers, attrs):
        cf_dict = attrgetter(attr)(device)
        cf_dict["serializer"] = serializer.pk
        device.device_type.manufacturer.save()
        device.device_type.save()
        device.save()
    return {d.pk: s.pk for d, s in zip(devices, serializers)}


@pytest.mark.django_db
def test_datasource_tenant(create_custom_fields):
    datasource = DataSourceFactory()
    tenant = TenantFactory(custom_field_data={"data_source": datasource.pk})
    DeviceFactory(tenant=tenant)
    device = VDevice.objects.prefetch_datasource().first()
    assert device.data_source == datasource


@pytest.mark.django_db
def test_datasource_default(create_custom_fields):
    datasource = DataSourceFactory(custom_field_data={"default": True})
    DeviceFactory()
    device = VDevice.objects.prefetch_datasource().first()
    assert device.data_source == datasource


@pytest.mark.django_db
def test_serializer(setup_serializers, subtests):
    device_serializer_map = setup_serializers
    devices = VDevice.objects.prefetch_serializer()
    for d in devices:
        with subtests.test(id=d.name):
            assert d.serializer.pk == device_serializer_map[d.pk]


@pytest.mark.parametrize("qs", [VDevice.objects.all(), VDevice.objects.filter(name__in=["d1", "d2"])])
@pytest.mark.django_db
def test_set_selector(qs, subtests):
    for name in ["d1", "d2", "d3"]:
        DeviceFactory(name=name)
    selector = SelectorFactory()
    qs = qs.set_selector(selector)
    for i, queryset in enumerate([qs, qs.select_related(), qs.filter(name="d1")]):
        with subtests.test(id=f"qs-{i}"):
            for model in queryset:
                assert model.selector == selector


def test_config_item(create_custom_fields):
    ds = DataSourceFactory(name="ds1", custom_field_data={"device_config_path": "path/{{device.name}}.txt"})
    data_file = DataFileFactory(source=ds, path="path/d1.txt")
    device = DeviceFactory(name="d1")
    device.serializer = SerializerDBFactory()
    device.data_source = ds
    assert device._config_item() == Serializable(device.serializer, data_file)
    device.data_source = None
    assert device._config_item() == Serializable(device.serializer, None)


@pytest.mark.django_db
def test_primary_ip():
    vdevice = DeviceFactory()
    device = Device.objects.get(pk=vdevice.pk)
    vdevice.primary_ip4 = device.primary_ip4 = IPAddress(address="1.1.1.1")
    vdevice.primary_ip6 = device.primary_ip6 = IPAddress(address="C0CA::BEEF")
    assert device.primary_ip == vdevice.primary_ip
    vdevice.prefer_ipv4 = True
    assert vdevice.primary_ip == vdevice.primary_ip4
    vdevice.prefer_ipv4 = False
    assert vdevice.primary_ip == vdevice.primary_ip6
