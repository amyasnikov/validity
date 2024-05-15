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
from validity.netbox_changes import CF_OBJ_TYPE, content_types


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
                required=False,
                **{CF_OBJ_TYPE: ContentType.objects.get_for_model(Serializer)},
            ),
            CustomField(
                name="data_source",
                type="object",
                required=False,
                **{CF_OBJ_TYPE: ContentType.objects.get_for_model(DataSource)},
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
                required=False,
                **{CF_OBJ_TYPE: ContentType.objects.get_for_model(Poller)},
            ),
        ]
    )
    content_types(cfs[0]).set(
        [
            ContentType.objects.get_for_model(Device).pk,
            ContentType.objects.get_for_model(DeviceType).pk,
            ContentType.objects.get_for_model(Manufacturer).pk,
        ]
    )
    content_types(cfs[1]).set([ContentType.objects.get_for_model(Tenant).pk])
    for cf in cfs[2:6]:
        content_types(cf).set([ContentType.objects.get_for_model(DataSource).pk])
    content_types(cfs[6]).set(
        [
            ContentType.objects.get_for_model(Device).pk,
            ContentType.objects.get_for_model(DeviceType).pk,
            ContentType.objects.get_for_model(Manufacturer).pk,
        ]
    )


@pytest.fixture
def gql_query(admin_client):
    def func(*args, **kwargs):
        return graphql_query(*args, **kwargs, client=admin_client, graphql_url="/graphql/")

    return func
