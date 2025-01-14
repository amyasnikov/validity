from pathlib import Path

import pytest
from core.models import DataSource
from dcim.models import Device, DeviceType, Manufacturer
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from extras.models import CustomField
from graphene_django.utils.testing import graphql_query
from tenancy.models import Tenant

import validity
import validity.scripts
from validity.models import Poller, Serializer
from validity.utils.orm import CustomFieldBuilder


pytest.register_assert_rewrite("base")


@pytest.fixture
def tests_root():
    return Path(validity.__file__).parent.absolute() / "tests"


@pytest.fixture
def create_custom_fields(db):
    cf_builder = CustomFieldBuilder(cf_model=CustomField, content_type_model=ContentType)

    cf_builder.create(
        name="serializer",
        type="object",
        required=False,
        object_type=ContentType.objects.get_for_model(Serializer),
        bind_to=[Device, DeviceType, Manufacturer],
    )
    cf_builder.create(
        name="default",
        type="boolean",
        required=False,
        default=False,
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="device_config_path",
        type="text",
        required=False,
        validation_regex=r"^[^/].*$",
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="device_command_path",
        type="text",
        required=False,
        validation_regex=r"^[^/].*$",
        weight=105,
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="web_url",
        type="text",
        required=False,
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="data_source",
        type="object",
        required=False,
        object_type=ContentType.objects.get_for_model(DataSource),
        bind_to=[Tenant],
    )
    cf_builder.create(
        name="poller",
        type="object",
        required=False,
        object_type=ContentType.objects.get_for_model(Poller),
        bind_to=[Device, DeviceType, Manufacturer],
    )


@pytest.fixture
def gql_query(admin_client):
    def func(*args, **kwargs):
        return graphql_query(*args, **kwargs, client=admin_client, graphql_url="/graphql/")

    return func


@pytest.fixture
def di():
    return validity.di


@pytest.fixture
def timezone_now(monkeypatch):
    def _now(tz):
        monkeypatch.setattr(timezone, "now", lambda: tz)

    return _now
