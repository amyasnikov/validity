from itertools import chain
from django.db import migrations
from django.utils.translation import gettext_lazy as _
from validity.fields.encrypted import EncryptedString
from django.db import migrations, models
import django.db.models.deletion


def setup_datasource_cf(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    DataSource = apps.get_model("core", "DataSource")
    Tenant = apps.get_model("tenancy", "Tenant")
    db = schema_editor.connection.alias
    datasource_cfs = CustomField.objects.using(db).bulk_create(
        [
            CustomField(
                name="default",
                label=_("Default DataSource"),
                description=_("Required by Validity"),
                type="boolean",
                required=False,
                default=False,
            ),
            CustomField(
                name="device_config_path",
                label=_("Device Config Path"),
                description=_("Required by Validity. J2 syntax allowed, e.g. devices/{{device.name}}.txt"),
                type="text",
                required=False,
                validation_regex=r"^[^/].*$",
            ),
            CustomField(
                name="device_command_path",
                label=_("Device Command Path"),
                description=_("Required by Validity. J2 syntax allowed, e.g. {{device.name}}/{{command.label}}.txt"),
                type="text",
                required=False,
                validation_regex=r"^[^/].*$",
                weight=105,
            ),
            CustomField(
                name="web_url",
                label=_("Web URL"),
                description=_("Required by Validity. You may use {{branch}} substitution"),
                type="text",
                required=False,
            ),
        ]
    )
    for cf in datasource_cfs:
        cf.content_types.set([ContentType.objects.get_for_model(DataSource)])
    tenant_cf = CustomField.objects.using(db).create(
        name="data_source",
        label=_("Data Source"),
        description=_("Required by Validity"),
        type="object",
        object_type=ContentType.objects.get_for_model(DataSource),
        required=False,
    )
    tenant_cf.content_types.set([ContentType.objects.get_for_model(Tenant)])


def delete_datasource_cf(apps, schema_editor):
    CustomField = apps.get_model("extras", "CustomField")
    CustomField.objects.using(schema_editor.connection.alias).filter(
        name__in=[
            "default",
            "device_config_path",
            "web_url",
        ],
        content_types__model="datasource",
    ).delete()


def get_fields(model, fields):
    result = {}
    for field_name in fields:
        if field_value := getattr(model, field_name, None):
            mapped_field_name = fields[field_name] if isinstance(fields, dict) else field_name
            result[mapped_field_name] = field_value
    return result


def setup_datasources(apps, schema_editor):
    from validity.models import VDataSource

    db = schema_editor.connection.alias
    GitRepo = apps.get_model("validity", "GitRepo")
    datasources = []
    for repo in GitRepo.objects.using(db).all():
        try:
            cf = get_fields(repo, ["web_url", "device_config_path", "default"])
            parameters = get_fields(repo, ["username", "branch", "encrypted_password"])
            if encrypted_password := parameters.pop("encrypted_password", None):
                parameters["password"] = EncryptedString.deserialize(encrypted_password).decrypt()
            datasource = VDataSource.objects.using(db).create(
                type="git",
                name="validity_" + repo.name,
                description=f"Auto-created by Validity from Git Repository {repo.name}",
                source_url=repo.git_url,
                parameters=parameters,
                custom_field_data=cf,
            )
            datasources.append(datasource)
        except Exception as e:
            print(
                f"\nAn error occured while creating Data Source for {repo.name}, skipping...",
                f"{type(e).__name__}: {e}",
                sep="\n",
            )  # noqa


def delete_repo_cf(apps, schema_editor):
    db = schema_editor.connection.alias
    CustomField = apps.get_model("extras", "CustomField")
    CustomField.objects.using(db).filter(name="repo", content_types__model="tenant").delete()


def setup_repo_cf(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    Tenant = apps.get_model("tenancy", "Tenant")
    GitRepo = apps.get_model("validity", "GitRepo")
    db = schema_editor.connection.alias

    cf = CustomField.objects.using(db).create(
        name="repo",
        label=_("Git Repository"),
        description=_("Required by Validity"),
        type="object",
        object_type=ContentType.objects.get_for_model(GitRepo),
        required=False,
    )
    cf.content_types.set([ContentType.objects.get_for_model(Tenant)])


def switch_git_links(apps, schema_editor):
    db = schema_editor.connection.alias
    DataSource = apps.get_model("core", "DataSource")
    DataFile = apps.get_model("core", "DataFile")
    models = [apps.get_model("validity", m) for m in ("ComplianceTest", "NameSet", "Serializer")]
    objects = chain.from_iterable(model.objects.all() for model in models)
    for obj in objects:
        if obj.repo is None:
            continue
        if not (
            data_source := DataSource.objects.using(db).filter(name="validity_" + obj.repo.name, type="git").first()
        ):
            continue
        obj.data_source = data_source
        if data_file := DataFile.objects.using(db).filter(source=data_source, path=obj.file_path).first():
            obj.data_file = data_file
        obj.save()


class Migration(migrations.Migration):
    dependencies = [("validity", "0005_rename_serializer"), ("core", "0001_initial")]

    operations = [
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
        migrations.AddField(
            model_name="compliancetest",
            name="data_file",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="validity.vdatafile",
            ),
        ),
        migrations.AddField(
            model_name="compliancetest",
            name="data_source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="validity.vdatasource",
            ),
        ),
        migrations.AddField(
            model_name="serializer",
            name="data_file",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="validity.vdatafile",
            ),
        ),
        migrations.AddField(
            model_name="serializer",
            name="data_source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="validity.vdatasource",
            ),
        ),
        migrations.AddField(
            model_name="nameset",
            name="data_file",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="validity.vdatafile",
            ),
        ),
        migrations.AddField(
            model_name="nameset",
            name="data_source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="validity.vdatasource",
            ),
        ),
        migrations.RunPython(setup_datasource_cf, delete_datasource_cf),
        migrations.RunPython(setup_datasources, migrations.RunPython.noop),
        migrations.RunPython(switch_git_links, migrations.RunPython.noop),
        migrations.RunPython(delete_repo_cf, setup_repo_cf),
        migrations.RemoveField(
            model_name="compliancetest",
            name="file_path",
        ),
        migrations.RemoveField(
            model_name="compliancetest",
            name="repo",
        ),
        migrations.RemoveField(
            model_name="serializer",
            name="file_path",
        ),
        migrations.RemoveField(
            model_name="serializer",
            name="repo",
        ),
        migrations.RemoveField(
            model_name="nameset",
            name="file_path",
        ),
        migrations.RemoveField(
            model_name="nameset",
            name="repo",
        ),
        migrations.DeleteModel(name="GitRepo"),
    ]
