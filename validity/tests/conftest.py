from pathlib import Path

import pytest
from core.models import DataSource
from dcim.models import Device, DeviceType, Manufacturer
from django.contrib.contenttypes.models import ContentType
from extras.models import CustomField
from graphene_django.utils.testing import graphql_query
from tenancy.models import Tenant

import validity
from validity.models import Poller, Serializer


pytest.register_assert_rewrite("base")


@pytest.fixture
def tests_root():
    return Path(validity.__file__).parent.absolute() / "tests"


@pytest.fixture
def create_custom_fields(db):
    cfs = CustomField.objects.bulk_create(
        [
            CustomField(
                name="serializer",
                type="object",
                object_type=ContentType.objects.get_for_model(Serializer),
                required=False,
            ),
            CustomField(
                name="data_source",
                type="object",
                object_type=ContentType.objects.get_for_model(DataSource),
                required=False,
            ),
            CustomField(
                name="default",
                type="boolean",
                required=False,
                default=False,
            ),
            CustomField(
                name="device_config_path",
                type="text",
                required=False,
            ),
            CustomField(
                name="web_url",
                type="text",
                required=False,
            ),
            CustomField(
                name="device_command_path",
                type="text",
                required=False,
            ),
            CustomField(
                name="poller",
                type="object",
                object_type=ContentType.objects.get_for_model(Poller),
                required=False,
            ),
        ]
    )
    cfs[0].content_types.set(
        [
            ContentType.objects.get_for_model(Device),
            ContentType.objects.get_for_model(DeviceType),
            ContentType.objects.get_for_model(Manufacturer),
        ]
    )
    cfs[1].content_types.set([ContentType.objects.get_for_model(Tenant)])
    for cf in cfs[2:6]:
        cf.content_types.set([ContentType.objects.get_for_model(DataSource)])
    cfs[6].content_types.set(
        [
            ContentType.objects.get_for_model(Device),
            ContentType.objects.get_for_model(DeviceType),
            ContentType.objects.get_for_model(Manufacturer),
        ]
    )


@pytest.fixture
def gql_query(admin_client):
    def func(*args, **kwargs):
        return graphql_query(*args, **kwargs, client=admin_client, graphql_url="/graphql/")

    return func
