from pathlib import Path

from django.db import migrations
from django.utils.translation import gettext_lazy as __
from validity import scripts


SCRIPTS_INSTALL_FOLDER = Path(scripts.__file__).parent.resolve() / "install"
DATASOURCE_NAME = "validity_scripts"
SCRIPT_NAME = "validity_scripts.py"


def forward_func(apps, schema_editor):
    from validity.models import VDataSource
    from extras.models import ScriptModule

    DataFile = apps.get_model("core", "DataFile")
    datasource, _ = VDataSource.objects.get_or_create(
        name=DATASOURCE_NAME,
        type="local",
        defaults={"source_url": f"file://{SCRIPTS_INSTALL_FOLDER.parent}", "description": __("Required by Validity")},
    )
    apps.get_model("core", "AutoSyncRecord").objects.filter(datafile__source__pk=datasource.pk).delete()
    ScriptModule.objects.filter(data_source=datasource).delete()
    datasource.source_url = f"file://{SCRIPTS_INSTALL_FOLDER}"
    datasource.save()
    datasource.sync_in_migration(DataFile)
    module = ScriptModule(
        data_source=datasource,
        data_file=datasource.datafiles.get(path=SCRIPT_NAME),
        file_root="scripts",
        auto_sync_enabled=True,
    )
    module.clean()
    module.save()


def reverse_func(apps, schema_editor):
    DataSource = apps.get_model("core", "DataSource")
    ScriptModule = apps.get_model("extras", "ScriptModule")
    db_alias = schema_editor.connection.alias
    ScriptModule.objects.using(db_alias).filter(data_source__name=DATASOURCE_NAME).delete()
    DataSource.objects.using(db_alias).filter(name=DATASOURCE_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("validity", "0007_polling"),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ]
