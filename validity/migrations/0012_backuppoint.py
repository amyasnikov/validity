# Generated by Django 5.0.10 on 2025-01-03 01:07

import django.core.validators
import django.db.models.deletion
import taggit.managers
import utilities.json
import validity.fields.encrypted
import validity.models.base
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('validity', '0011_delete_scripts'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('backup_after_sync', models.BooleanField()),
                ('method', models.CharField(max_length=20)),
                ('url', models.CharField(max_length=255, validators=[django.core.validators.URLValidator(schemes=['http', 'https'])])),
                ('ignore_rules', models.TextField(blank=True)),
                ('parameters', validity.fields.encrypted.EncryptedDictField(do_not_encrypt=('username', 'branch', 'aws_access_key_id', 'archive'))),
                ('last_uploaded', models.DateTimeField(blank=True, editable=False, null=True)),
                ('last_status', models.CharField(blank=True, editable=False)),
                ('last_error', models.CharField(blank=True, editable=False)),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='backup_points', to='validity.vdatasource')),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': 'Backup Point',
                'verbose_name_plural': 'Backup Points',
                'ordering': ('name',),
            },
            bases=(validity.models.base.SubformMixin, validity.models.base.URLMixin, models.Model),
        ),
    ]
