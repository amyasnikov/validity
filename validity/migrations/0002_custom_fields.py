from django.db import migrations
from django.utils.translation import gettext_lazy as _


def forward_func(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    Device = apps.get_model("dcim", "Device")
    DeviceType = apps.get_model("dcim", "DeviceType")
    Manufacturer = apps.get_model("dcim", "Manufacturer")
    ConfigSerializer = apps.get_model("validity", "ConfigSerializer")

    db_alias = schema_editor.connection.alias

    cfs = CustomField.objects.using(db_alias).bulk_create(
        [
            CustomField(
                name="config_serializer",
                label=_("Config Serializer"),
                type="object",
                object_type=ContentType.objects.get_for_model(ConfigSerializer),
                required=False,
            ),
            CustomField(
                name="config_path",
                label=_("Config Path"),
                description=_("Path to configuration file inside git repo (overrides default one)"),
                type="string",
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


def reverse_func(apps, schema_editor):
    CustomField = apps.get_model("extras", "CustomField")
    db_alias = schema_editor.connection.alias
    CustomField.objects.using(db_alias).filter(
        name__in=[
            "config_serializer",
            "config_path",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("validity", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ]
