# Generated by Django 4.1.5 on 2023-02-25 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validity", "0003_alter_compliancetestresult_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="complianceselector",
            options={"ordering": ("name",)},
        ),
        migrations.AlterModelOptions(
            name="configserializer",
            options={"ordering": ("name",)},
        ),
        migrations.AlterModelOptions(
            name="nameset",
            options={"ordering": ("name",)},
        ),
        migrations.AlterField(
            model_name="nameset",
            name="serializers",
            field=models.ManyToManyField(blank=True, related_name="namesets", to="validity.configserializer"),
        ),
    ]