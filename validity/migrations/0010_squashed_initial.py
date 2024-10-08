# Generated by Django 5.0.6 on 2024-05-12 22:17

import django.core.validators
import django.db.models.deletion
import taggit.managers
import utilities.json
import validity.fields.encrypted
import validity.models.base
import validity.models.test_result
from django.db import migrations, models
from django.utils.translation import gettext_lazy as __
from validity.utils.orm import CustomFieldBuilder



def create_cf(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    Device = apps.get_model("dcim", "Device")
    Tenant = apps.get_model("tenancy", "Tenant")
    DeviceType = apps.get_model("dcim", "DeviceType")
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    Serializer = apps.get_model("validity", "Serializer")
    Poller = apps.get_model("validity", "Poller")
    DataSource = apps.get_model("core", "DataSource")
    Tenant = apps.get_model("tenancy", "Tenant")
    db = schema_editor.connection.alias

    cf_builder = CustomFieldBuilder(cf_model=CustomField, content_type_model=ContentType, db_alias=db)

    cf_builder.create(
        name="serializer",
        label=__("Config Serializer"),
        description=__("Required by Validity"),
        type="object",
        required=False,
        object_type=ContentType.objects.get_for_model(Serializer),
        bind_to=[Device, DeviceType, Manufacturer],
    )
    cf_builder.create(
        name="default",
        label=__("Default DataSource"),
        description=__("Required by Validity"),
        type="boolean",
        required=False,
        default=False,
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="device_config_path",
        label=__("Device Config Path"),
        description=__("Required by Validity. J2 syntax allowed, e.g. devices/{{device.name}}.txt"),
        type="text",
        required=False,
        validation_regex=r"^[^/].*$",
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="device_command_path",
        label=__("Device Command Path"),
        description=__("Required by Validity. J2 syntax allowed, e.g. {{device.name}}/{{command.label}}.txt"),
        type="text",
        required=False,
        validation_regex=r"^[^/].*$",
        weight=105,
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="web_url",
        label=__("Web URL"),
        description=__("Required by Validity. You may use {{branch}} substitution"),
        type="text",
        required=False,
        bind_to=[DataSource],
    )
    cf_builder.create(
        name="data_source",
        label=__("Data Source"),
        description=__("Required by Validity"),
        type="object",
        required=False,
        object_type=ContentType.objects.get_for_model(DataSource),
        bind_to=[Tenant],
    )
    cf_builder.create(
        name="poller",
        type="object",
        label=__("Poller"),
        description=__("Required by Validity. Defines properties of device polling"),
        required=False,
        object_type=ContentType.objects.get_for_model(Poller),
        bind_to=[Device, DeviceType, Manufacturer]
    )


def delete_cf(apps, schema_editor):
    CustomField = apps.get_model("extras", "CustomField")
    db = schema_editor.connection.alias
    CustomField.objects.using(db).filter(
        name__in=["data_source", "web_url", "device_command_path", "device_config_path", "default", "serializer"]
    ).delete()


def create_polling_datasource(apps, schema_editor):
    DataSource = apps.get_model("core", "DataSource")
    db = schema_editor.connection.alias
    ds = DataSource.objects.using(db).create(
        name="Validity Polling",
        type="device_polling",
        source_url="/",
        description=__("Required by Validity. Polls bound devices and stores the results"),
        custom_field_data={
            "device_command_path": "{{device | slugify}}/{{ command.label }}.txt",
            "default": False,
            "web_url": "",
        },
    )
    ds.parameters = {"datasource_id": ds.pk}
    ds.save()


def delete_polling_datasource(apps, schema_editor):
    DataSource = apps.get_model("core", "DataSource")
    db = schema_editor.connection.alias
    DataSource.objects.using(db).filter(type="Validity Polling").delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0001_initial"),
        ("dcim", "0167_module_status"),
        ("extras", "0084_staging"),
        ("tenancy", "0009_standardize_description_comments"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplianceReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ComplianceSelector",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("filter_operation", models.CharField(default="AND", max_length=3)),
                ("name_filter", models.CharField(blank=True, max_length=255)),
                ("status_filter", models.CharField(blank=True, max_length=50)),
                ("dynamic_pairs", models.CharField(default="NO", max_length=20)),
                ("location_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.location")),
                ("manufacturer_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.manufacturer")),
                ("platform_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.platform")),
                ("site_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.site")),
                ("tag_filter", models.ManyToManyField(blank=True, related_name="+", to="extras.tag")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                ("tenant_filter", models.ManyToManyField(blank=True, related_name="+", to="tenancy.tenant")),
                ("type_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.devicetype")),
                ("dp_tag_prefix", models.CharField(blank=True, max_length=255)),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="VDataFile",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("core.datafile",),
        ),
        migrations.CreateModel(
            name="VDataSource",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("core.datasource",),
        ),
        migrations.CreateModel(
            name="ComplianceTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField()),
                ("severity", models.CharField(default="MIDDLE", max_length=10)),
                ("expression", models.TextField(blank=True)),
                ("selectors", models.ManyToManyField(related_name="tests", to="validity.complianceselector")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                (
                    "data_file",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="validity.vdatafile",
                    ),
                ),
                (
                    "data_source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="validity.vdatasource",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "ordering": ("name",),
                "permissions": [("run", "Can run compliance test")],
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="VDevice",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("dcim.device",),
        ),
        migrations.CreateModel(
            name="ComplianceTestResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("passed", models.BooleanField()),
                (
                    "explanation",
                    models.JSONField(blank=True, default=list, encoder=validity.models.test_result.DeepDiffEncoder),
                ),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="results", to="validity.vdevice"
                    ),
                ),
                (
                    "dynamic_pair",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="validity.vdevice",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="validity.compliancereport",
                    ),
                ),
                (
                    "test",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="validity.compliancetest",
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Serializer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("extraction_method", models.CharField(max_length=10)),
                ("template", models.TextField(blank=True)),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                (
                    "data_file",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="validity.vdatafile",
                    ),
                ),
                (
                    "data_source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="validity.vdatasource",
                    ),
                ),
                ("parameters", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ("name",),
                "default_permissions": (),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="NameSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField()),
                ("_global", models.BooleanField(blank=True, default=False)),
                ("definitions", models.TextField(blank=True)),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                ("tests", models.ManyToManyField(blank=True, related_name="namesets", to="validity.compliancetest")),
                (
                    "data_file",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="validity.vdatafile",
                    ),
                ),
                (
                    "data_source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="validity.vdatasource",
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Command",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "label",
                    models.CharField(
                        max_length=100,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Only lowercase ASCII letters, numbers and underscores are allowed",
                                regex="^[a-z][a-z0-9_]*$",
                            ),
                            django.core.validators.RegexValidator(
                                inverse_match=True, message="This label name is reserved", regex="^config$"
                            ),
                        ],
                    ),
                ),
                ("retrieves_config", models.BooleanField(default=False)),
                (
                    "serializer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="commands",
                        to="validity.serializer",
                    ),
                ),
                ("type", models.CharField(max_length=50)),
                ("parameters", models.JSONField()),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Poller",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("connection_type", models.CharField(max_length=50)),
                ("public_credentials", models.JSONField(blank=True, default=dict)),
                ("private_credentials", validity.fields.encrypted.EncryptedDictField(blank=True)),
                ("commands", models.ManyToManyField(related_name="pollers", to="validity.command")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.RunPython(create_cf, delete_cf),
        migrations.RunPython(create_polling_datasource, delete_polling_datasource),
    ]
