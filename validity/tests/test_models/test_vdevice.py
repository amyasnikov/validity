import pytest
from django.db import connection
from factories import DeviceFactory, GitRepoFactory, SelectorFactory, SerializerDBFactory, TenantFactory

from validity.models import VDevice


@pytest.fixture
def setup_device_and_serializer(create_custom_fields):
    serializer = SerializerDBFactory()
    device = DeviceFactory()
    device.device_type.custom_field_data["serializer"] = serializer.pk
    device.device_type.save()
    return device, serializer


@pytest.fixture
def setup_device_and_repo(create_custom_fields):
    repo = GitRepoFactory()
    tenant = TenantFactory()
    tenant.custom_field_data["repo"] = repo.id
    tenant.save()
    device = DeviceFactory(tenant=tenant)
    return device, repo


@pytest.mark.django_db
def test_adhoc_tenant_repo(setup_device_and_repo):
    device, repo = setup_device_and_repo
    vdevice = VDevice.objects.get(pk=device.pk)
    assert vdevice.repo == repo


@pytest.mark.django_db
def test_annotated_tenant_repo(setup_device_and_repo):
    device, repo = setup_device_and_repo
    vdevice = VDevice.objects.annotate_json_repo().get(pk=device.pk)
    queries_count = len(connection.queries)
    assert vdevice.repo == repo
    assert len(connection.queries) == queries_count


@pytest.mark.django_db
def test_adhoc_default_repo():
    repo = GitRepoFactory(default=True)
    device = DeviceFactory()
    assert device.repo == repo


@pytest.mark.django_db
def test_annotated_default_repo():
    repo = GitRepoFactory(default=True)
    device_pk = DeviceFactory().pk
    device = VDevice.objects.annotate_json_repo().get(pk=device_pk)
    queries_count = len(connection.queries)
    assert device.repo == repo
    assert len(connection.queries) == queries_count


@pytest.mark.django_db
def test_adhoc_serializer(setup_device_and_serializer):
    device, serializer = setup_device_and_serializer
    vdevice = VDevice.objects.get(pk=device.pk)
    assert vdevice.serializer == serializer


@pytest.mark.django_db
def test_annotated_serializer(setup_device_and_serializer):
    device, serializer = setup_device_and_serializer
    vdevice = VDevice.objects.annotate_json_serializer().get(pk=device.pk)
    queries_count = len(connection.queries)
    assert vdevice.serializer == serializer
    assert len(connection.queries) == queries_count


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
