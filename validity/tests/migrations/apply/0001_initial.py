from django.contrib.postgres.operations import CreateCollation, CreateExtension
from django.db import migrations
import sys


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        CreateCollation('natural_sort', provider='icu', locale='und-u-kn-true'),
        CreateExtension('ltree'),
    ]
