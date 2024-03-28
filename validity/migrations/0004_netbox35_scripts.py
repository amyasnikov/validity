from django.db import migrations


def forward_func(apps, schema_editor):
    """
    Migration has been removed due to better approach implemented in 0008_script_change
    """


class Migration(migrations.Migration):
    dependencies = [
        ("validity", "0003_complianceselector_dp_tag_prefix"),
    ]

    operations = [
        migrations.RunPython(forward_func, migrations.RunPython.noop),
    ]
