from django.db import migrations
from django.utils.translation import gettext_lazy as _


def setup_datasource_cf(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    DataSource = apps.get_model("core", "DataSource")
    Tenant = apps.get_model("tenancy", "Tenant")
    db = schema_editor.connection.alias
    datasource_cfs = CustomField.objects.using(db).bulk_create(
        [
            CustomField(
                name="device_config_default",
                label=_("Default for Device Configs"),
                description=_("Required by Validity"),
                type="boolean",
                required=False,
                default=False,
            ),
            CustomField(
                name="device_config_path",
                label=_("Device Config Path"),
                description=_("Required by Validity. J2 syntax allowed, e.g. devices/{{device.name}}.txt"),
                type="string",
                required=False,
                validation_regex=r"^[^/].*$",
            ),
            CustomField(
                name="web_url_template",
                label=_("Web URL Template"),
                description=_("Required by Validity. You may use {{branch}} substitution"),
                type="string",
                required=False,
            ),
        ]
    )
    for cf in datasource_cfs:
        cf.content_types.set([ContentType.objects.using(db).get_for_model(DataSource)])
    tenant_cf = CustomField.objects.using(db).create(
        name='config_data_source',
        label=_('Config Data Source'),
        description=_("Required by Validity"),
        type='object',
        object_type=ContentType.objects.get_for_model(DataSource),
        required=False,
    )
    tenant_cf.content_types.set([ContentType.objects.using(db).get_for_model(Tenant)])


def delete_datasource_cf(apps, schema_editor):
    CustomField = apps.get_model("extras", "CustomField")
    CustomField.objects.using(schema_editor.connection.alias).filter(
        name__in=[
            "device_config_default",
            "device_config_path",
            "web_url_template",
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
    from core.models import DataSource

    db = schema_editor.connection.alias
    GitRepo = apps.get_model("validity", "GitRepo")
    for repo in GitRepo.objects.using(db).all():
        try:
            cf = get_fields(
                repo,
                {
                    "web_url": "web_url_template",
                    "device_config_path": "device_config_path",
                    "default": "device_config_default",
                },
            )
            datasource = DataSource.objects.using(db).create(
                type="git",
                name=repo.name,
                description=repo.description,
                source_url=repo.git_url,
                parameters=get_fields(repo, ["username", "password", "branch"]),
                custom_field_data=cf,
            )
            datasource.sync()
        except Exception as e:
            print(f"An error occured while creating Data Source for {repo}, skipping.", type(e).__name__, e)  # noqa


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
    DataSource = apps.get_model('core', 'DataSource')
    DataFile = apps.get_model('core', 'DataFile')
    models = [apps.get_model('validity', m) for m in ('ComplianceTest', 'NameSet', 'ConfigSerializer')]
    for model in models:
        if model.repo is None:
            continue
        if not (data_source := DataSource.objects.using(db).filter(name=model.repo.name).first()):
            continue
        model.data_source = data_source
        if data_file := DataFile.objects.using(db).filter(source=data_source, path=model.repo.file_path).first():
            model.data_file = data_file
        model.save()


class Migration(migrations.Migration):
    dependencies = [("validity", "0004_netbox35_scripts"), ("core", "0001_initial")]

    operations = [
        migrations.RunPython(setup_datasource_cf, delete_datasource_cf),
        migrations.RunPython(setup_datasources, migrations.RunPython.noop),
        migrations.RunPython(switch_git_links, migrations.RunPython.noop),
        migrations.RunPython(delete_repo_cf, setup_repo_cf),
        migrations.DeleteModel(name="GitRepo"),
    ]
