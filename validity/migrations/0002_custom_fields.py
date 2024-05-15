from django.db import migrations
from django.utils.translation import gettext_lazy as _
from validity.netbox_changes import CF_OBJ_TYPE, content_types

def forward_func(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    Device = apps.get_model("dcim", "Device")
    Tenant = apps.get_model("tenancy", "Tenant")
    DeviceType = apps.get_model("dcim", "DeviceType")
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    ConfigSerializer = apps.get_model("validity", "ConfigSerializer")
    GitRepo = apps.get_model("validity", "GitRepo")

    db_alias = schema_editor.connection.alias

    cfs = CustomField.objects.using(db_alias).bulk_create(
        [
            CustomField(
                name="serializer",
                label=_("Config Serializer"),
                description=_("Required by Validity"),
                type="object",
                required=False,
                **{CF_OBJ_TYPE: ContentType.objects.get_for_model(ConfigSerializer)},
            ),
            CustomField(
                name="repo",
                label=_("Git Repository"),
                description=_("Required by Validity"),
                type="object",
                required=False,
                **{CF_OBJ_TYPE: ContentType.objects.get_for_model(GitRepo)},
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


def reverse_func(apps, schema_editor):
    CustomField = apps.get_model("extras", "CustomField")
    db_alias = schema_editor.connection.alias
    CustomField.objects.using(db_alias).filter(
        name__in=[
            "serializer",
            "repo",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("validity", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ]
