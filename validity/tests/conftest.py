from contextlib import contextmanager
from pathlib import Path

import pytest
from core.models import DataSource
from dcim.models import Device, DeviceType, Manufacturer
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.test.utils import setup_databases, teardown_databases
from django.utils import timezone
from extras.models import CustomField
from graphene_django.utils.testing import graphql_query
from tenancy.models import Tenant

import validity
import validity.scripts
from validity import dependencies
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


@pytest.fixture
def launcher_factory(di):
    return di[dependencies.launcher_factory]


@contextmanager
def _setup_migrations(use_test_migrations):
    class UseTestMigrations:
        def __init__(self, getitem_fn):
            self.getitem_fn = getitem_fn

        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return self.getitem_fn(item)

    if use_test_migrations:
        settings.MIGRATION_MODULES = UseTestMigrations(
            lambda app: "migrations.apply" if app == "validity" else "migrations.dont_apply"
        )
    yield
    if use_test_migrations:
        settings.MIGRATION_MODULES = UseTestMigrations(
            lambda app: None
        )  # force creating the tables according to the models
        call_command("migrate", interactive=False, database=connection.alias, run_syncdb=True)
        settings.MIGRATION_MODULES = {}


@pytest.fixture(scope="session")
def django_db_setup(request, django_test_environment, django_db_blocker, django_db_use_migrations):
    """
    This is the override of pytest-django native fixture.
    It allows create the collation first and only then create the tables (many of netbox models require that collation)
    """

    with django_db_blocker.unblock(), _setup_migrations(use_test_migrations=not django_db_use_migrations):
        db_cfg = setup_databases(verbosity=request.config.option.verbose, interactive=False, serialized_aliases=[])
    yield

    with django_db_blocker.unblock():
        try:
            teardown_databases(db_cfg, verbosity=request.config.option.verbose)
        except Exception as exc:
            request.node.warn(pytest.PytestWarning(f"Error when trying to teardown test databases: {exc!r}"))
