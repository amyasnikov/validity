# Generated by Django 4.1.5 on 2023-03-12 09:51

from django.db import migrations, models
import django.db.models.deletion
import utilities.json
import validity.models.base


class Migration(migrations.Migration):

    dependencies = [
        ("validity", "0009_compliancetest_file_path_compliancetest_repo_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplianceReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                "abstract": False,
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.AlterModelOptions(
            name="gitrepo",
            options={"verbose_name": "Git Repository", "verbose_name_plural": "Git Repositories"},
        ),
        migrations.AlterField(
            model_name="compliancetest",
            name="expression",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="compliancetest",
            name="file_path",
            field=models.CharField(blank=True, max_length=255, validators=[validity.models.base.validate_file_path]),
        ),
        migrations.AlterField(
            model_name="configserializer",
            name="file_path",
            field=models.CharField(blank=True, max_length=255, validators=[validity.models.base.validate_file_path]),
        ),
        migrations.AlterField(
            model_name="configserializer",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="gitrepo",
            name="device_config_path",
            field=models.CharField(max_length=255, validators=[validity.models.base.validate_file_path]),
        ),
        migrations.AlterField(
            model_name="nameset",
            name="definitions",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="nameset",
            name="file_path",
            field=models.CharField(blank=True, max_length=255, validators=[validity.models.base.validate_file_path]),
        ),
        migrations.AddField(
            model_name="compliancetestresult",
            name="report",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="results",
                to="validity.compliancereport",
            ),
        ),
    ]
