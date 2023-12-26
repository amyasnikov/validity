from operator import attrgetter

import pytest
from factories import (
    ConfigFileFactory,
    DataSourceFactory,
    DeviceFactory,
    SelectorFactory,
    SerializerDBFactory,
    TenantFactory,
)

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
    tenant = TenantFactory(custom_field_data={"config_data_source": datasource.pk})
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
def test_data_file(create_custom_fields):
    DeviceFactory()
    data_file = ConfigFileFactory()
    device = VDevice.objects.prefetch_datasource().first()
    assert device.data_file == data_file


@pytest.mark.django_db
def test_serializer(setup_serializers, subtests):
    device_serializer_map = setup_serializers
    devices = VDevice.objects.prefetch_serializer()
    for d in devices:
        with subtests.test(id=d.name):
            assert d.serializer.pk == device_serializer_map[d.pk]


@pytest.mark.django_db
def test_config_path(create_custom_fields):
    DeviceFactory(name="device1")
    DataSourceFactory(custom_field_data={"device_config_path": "path/{{device.name}}.cfg", "default": True})
    device = VDevice.objects.prefetch_datasource().first()
    assert device.config_path == "path/device1.cfg"


@pytest.mark.parametrize("qs", [VDevice.objects.all(), VDevice.objects.filter(name__in=["d1", "d2"])])
@pytest.mark.django_db
def test_set_selector(qs, subtests):
    for name in ["d1", "d2", "d3"]:
        DeviceFactory(name=name)
    selector = SelectorFactory()
    some_model = qs.first()
    assert some_model.selector is None
    qs = qs.set_selector(selector)
    for i, queryset in enumerate([qs, qs.select_related(), qs.filter(name="d1")]):
        with subtests.test(id=f"qs-{i}"):
            for model in queryset:
                assert model.selector == selector
