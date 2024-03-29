# Generated by Django 2.0.2 on 2018-02-19 08:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("automated_logging", "0013_auto_20180218_1106"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="status",
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.RemoveField(model_name="field", name="model"),
        migrations.AddField(
            model_name="field",
            name="model",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dal_field",
                to="contenttypes.ContentType",
            ),
        ),
        migrations.DeleteModel(
            name="ModelStorage",
        ),
    ]
