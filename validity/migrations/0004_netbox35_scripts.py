from pathlib import Path
import sys

from django.db import IntegrityError, migrations, transaction
from django.utils.translation import gettext_lazy as _
from validity import scripts
from validity import config


SCRIPTS_FOLDER = str(Path(scripts.__file__).parent.resolve())
DATASOURCE_NAME = "validity_scripts"


def forward_func(apps, schema_editor):
    if config.netbox_version < "3.5.0":
        return

    from validity.models import VDataSource
    from extras.models import ScriptModule

    db_alias = schema_editor.connection.alias
    data_source = VDataSource.objects.using(db_alias).create(
        name=DATASOURCE_NAME, type="local", source_url="file://" + SCRIPTS_FOLDER, description=_("Required by Validity")
    )
    DataFile = apps.get_model("core", "DataFile")
    data_source.sync_in_migration(DataFile)
    for data_file in data_source.datafiles.using(db_alias).all():
        if data_file.path.endswith("__init__.py") or data_file.path.endswith(".pyc"):
            continue
        module = ScriptModule(data_source=data_source, data_file=data_file, file_root="scripts", auto_sync_enabled=True)
        module.clean()
        try:
            with transaction.atomic():
                module.save()
        except IntegrityError:
            print(f"\n{module.full_path} already exists, ignoring", file=sys.stderr)  # noqa


def reverse_func(apps, schema_editor):
    if config.netbox_version < "3.5.0":
        return
    DataSource = apps.get_model("core", "DataSource")
    ScriptModule = apps.get_model("extras", "ScriptModule")
    db_alias = schema_editor.connection.alias
    ScriptModule.objects.using(db_alias).filter(data_source__name=DATASOURCE_NAME).delete()
    DataSource.objects.using(db_alias).filter(name=DATASOURCE_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("validity", "0003_complianceselector_dp_tag_prefix"),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
    ]
