from django.contrib.postgres.operations import CreateCollation
from django.db import migrations
import sys


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        CreateCollation('natural_sort', provider='icu', locale='und-u-kn-true'),
    ]
