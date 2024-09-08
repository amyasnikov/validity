from django.db import migrations


DATASOURCE_NAME = "validity_scripts"


def delete_scripts(apps, schema_editor):
    """
    Delete DataSource and ScriptModule used for validity v1/v2
    """
    DataSource = apps.get_model("core", "DataSource")
    ScriptModule = apps.get_model("extras", "ScriptModule")
    db_alias = schema_editor.connection.alias
    ScriptModule.objects.using(db_alias).filter(data_source__name=DATASOURCE_NAME).delete()
    DataSource.objects.using(db_alias).filter(name=DATASOURCE_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("validity", "0010_squashed_initial"),
    ]
    operations = [
        migrations.RunPython(delete_scripts, migrations.RunPython.noop),
    ]
