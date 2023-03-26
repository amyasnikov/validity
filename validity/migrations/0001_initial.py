# Generated by Django 4.1.5 on 2023-03-22 17:20

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import utilities.json
import validity.models.base
import validity.utils.password
import validity.models.test_result


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("extras", "0084_staging"),
        ("dcim", "0167_module_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComplianceReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ComplianceSelector",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("filter_operation", models.CharField(default="AND", max_length=3)),
                ("name_filter", models.CharField(blank=True, max_length=255)),
                ("status_filter", models.CharField(blank=True, max_length=50)),
                ("dynamic_pairs", models.CharField(default="NO", max_length=20)),
                ("location_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.location")),
                ("manufacturer_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.manufacturer")),
                ("platform_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.platform")),
                ("site_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.site")),
                ("tag_filter", models.ManyToManyField(blank=True, related_name="+", to="extras.tag")),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                ("type_filter", models.ManyToManyField(blank=True, related_name="+", to="dcim.devicetype")),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ComplianceTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "file_path",
                    models.CharField(blank=True, max_length=255, validators=[validity.models.base.validate_file_path]),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField()),
                ("severity", models.CharField(default="MIDDLE", max_length=10)),
                ("expression", models.TextField(blank=True)),
            ],
            options={
                "abstract": False,
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="GitRepo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("name", models.CharField(blank=True, max_length=255, unique=True)),
                ("git_url", models.CharField(max_length=255, validators=[django.core.validators.URLValidator()])),
                ("web_url", models.CharField(blank=True, max_length=255)),
                (
                    "device_config_path",
                    models.CharField(max_length=255, validators=[validity.models.base.validate_file_path]),
                ),
                ("default", models.BooleanField(default=False)),
                ("username", models.CharField(blank=True, max_length=255)),
                ("encrypted_password", validity.utils.password.PasswordField(blank=True, default=None, null=True)),
                (
                    "branch",
                    models.CharField(
                        blank=True,
                        default="master",
                        max_length=255,
                        validators=[django.core.validators.RegexValidator("[a-zA-Z_-]*")],
                    ),
                ),
                ("head_hash", models.CharField(blank=True, max_length=40)),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "verbose_name": "Git Repository",
                "verbose_name_plural": "Git Repositories",
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="NameSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "file_path",
                    models.CharField(blank=True, max_length=255, validators=[validity.models.base.validate_file_path]),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField()),
                ("_global", models.BooleanField(blank=True, default=False)),
                ("definitions", models.TextField(blank=True)),
                (
                    "repo",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="validity.gitrepo"
                    ),
                ),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
                ("tests", models.ManyToManyField(blank=True, related_name="namesets", to="validity.compliancetest")),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ConfigSerializer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                (
                    "file_path",
                    models.CharField(blank=True, max_length=255, validators=[validity.models.base.validate_file_path]),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("extraction_method", models.CharField(default="TTP", max_length=10)),
                ("ttp_template", models.TextField(blank=True)),
                (
                    "repo",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="validity.gitrepo"
                    ),
                ),
                ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag")),
            ],
            options={
                "ordering": ("name",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.CreateModel(
            name="ComplianceTestResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                ("passed", models.BooleanField()),
                ("explanation", models.JSONField(default=list, encoder=validity.models.test_result.DeepDiffEncoder)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="results", to="dcim.device"
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="validity.compliancereport",
                    ),
                ),
                (
                    "test",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="validity.compliancetest",
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
            },
            bases=(validity.models.base.URLMixin, models.Model),
        ),
        migrations.AddField(
            model_name="compliancetest",
            name="repo",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="validity.gitrepo"
            ),
        ),
        migrations.AddField(
            model_name="compliancetest",
            name="selectors",
            field=models.ManyToManyField(related_name="tests", to="validity.complianceselector"),
        ),
        migrations.AddField(
            model_name="compliancetest",
            name="tags",
            field=taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
        ),
    ]
