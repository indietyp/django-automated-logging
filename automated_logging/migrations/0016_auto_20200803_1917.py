# Generated by Django 3.0.7 on 2020-08-03 19:17
# Edited by Bilal Mahmoud for 5.x.x to 6.x.x conversion

from django.db import migrations
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import picklefield.fields
import uuid
import os

import logging

logger = logging.getLogger(__name__)


def convert(apps, schema_editor):
    """convert from 5.x.x to 6.x.x"""
    if os.environ.get("DAL_SKIP_CONVERSION", "").lower() == "true":
        logger.info("Skipping conversion")
        return

    alias = schema_editor.connection.alias

    # convert all new applications
    logger.info("Converting Applications from 5.x.x to 6.x.x")
    # Application does not change, except new unknown Application
    Application = apps.get_model("automated_logging", "Application")
    applications = [Application(name=None)]
    no_application = applications[0]

    # convert request events
    logger.info("Converting Request Events from 5.x.x to 6.x.x")
    RequestOld = apps.get_model("automated_logging", "Request")
    RequestEvent = apps.get_model("automated_logging", "RequestEvent")
    requests = [
        RequestEvent(
            id=r.id,
            created_at=r.created_at,
            updated_at=r.updated_at,
            user=r.user,
            uri=str(r.uri),
            method=r.method[:32],
            status=r.status,
            application=(
                Application.objects.using(alias).get(id=r.application.id)
                if r.application
                else no_application
            ),
        )
        for r in RequestOld.objects.using(alias).all()
    ]

    # convert unspecified events
    logger.info("Converting Unspecified Events from 5.x.x to 6.x.x")
    UnspecifiedOld = apps.get_model("automated_logging", "Unspecified")
    UnspecifiedEvent = apps.get_model("automated_logging", "UnspecifiedEvent")
    unspecified = [
        UnspecifiedEvent(
            id=u.id,
            created_at=u.created_at,
            updated_at=u.updated_at,
            message=u.message,
            level=u.level,
            file=u.file,
            line=u.line,
            application=no_application,
        )
        for u in UnspecifiedOld.objects.using(alias).all()
    ]

    # convert model events
    logger.info(
        "Converting Models Events from 5.x.x to 6.x.x (This might take a while)"
    )
    ModelOld = apps.get_model("automated_logging", "Model")
    ModelEvent = apps.get_model("automated_logging", "ModelEvent")

    ModelMirror = apps.get_model("automated_logging", "ModelMirror")
    ModelEntry = apps.get_model("automated_logging", "ModelEntry")
    ModelField = apps.get_model("automated_logging", "ModelField")
    ModelRelationshipModification = apps.get_model(
        "automated_logging", "ModelRelationshipModification"
    )
    ModelValueModification = apps.get_model(
        "automated_logging", "ModelValueModification"
    )

    mirrors = [ModelMirror(name="", application=no_application)]
    no_mirror = mirrors[0]

    entries = [ModelEntry(value="", primary_key="", mirror=no_mirror)]
    no_entry = entries[0]

    fields = [ModelField(name="", mirror=no_mirror, type="")]
    no_field = fields[0]

    events = []

    value_modifications = []
    relationship_modifications = []

    def get_application(content_type):
        """
        simple helper function to get a new application from a content type
        :return: ApplicationNew
        """
        app = next(
            (a for a in applications if a.name == content_type.app_label),
            None,
        )

        if not app:
            app = Application(name=content_type.app_label)
            applications.append(app)

        return app

    def get_mirror(content_type):
        """
        simple helper function to get the new mirror from content type
        :return: ModelMirror
        """
        app = get_application(content_type)
        mir = next((m for m in mirrors if m.name == content_type.model), None)
        if not mir:
            mir = ModelMirror(name=content_type.model, application=app)
            mirrors.append(mir)

        return mir

    def get_entry(value, mir):
        """
        simple helper function to find the appropriate entry
        :return: ModelEntry
        """
        ent = next((e for e in entries if e.value == value), None)
        if not ent:
            ent = ModelEntry(value=value, primary_key="", mirror=mir)
            entries.append(ent)
        return ent

    def get_field(target):
        """
        simple inline helper function to get the correct field
        :return: ModelField
        """

        if target is None:
            return no_field

        app = get_application(target.model)

        mir = next(
            (m for m in mirrors if m.application.name == target.model.app_label),
            None,
        )
        if not mir:
            mir = ModelMirror(name=target.model.model, application=app)

        fie = next(
            (e for e in fields if e.name == target.name and e.mirror == mir),
            None,
        )
        if not fie:
            fie = ModelField(name=target.name, mirror=mir, type="<UNKNOWN>")
            fields.append(fie)

        return fie

    oldies = ModelOld.objects.using(alias).all()

    progress = oldies.count() // 10
    idx = 0
    for old in oldies:
        event = ModelEvent(
            id=old.id, created_at=old.created_at, updated_at=old.updated_at
        )

        # converting old.information
        # old.information -> event.model
        #   value => value
        #   content_type => ModelMirror
        #       app_label => Application
        #       model => ModelMirror.name
        # provide some defaults, so that if no content_type is there
        # the program doesn't poo all over the floor.
        entry = no_entry
        if old.information:
            mirror = no_mirror

            # there is a chance old.information.type is null,
            # we need to check for that case
            if old.information.type:
                mirror = get_mirror(old.information.type)

            entry = next((e for e in entries if e.value == old.information.value), None)
            if not entry:
                entry = ModelEntry(
                    value=old.information.value, primary_key="", mirror=mirror
                )
                entries.append(entry)
        event.entry = entry

        ACTION_TRANSLATIONS = {0: None, 1: 1, 2: 0, 3: -1}

        # old.modification -> event.modifications, event.relationships
        # if information has content_type then relationship, else modification
        # problem: field is unknown
        #   modification => modifications
        #       operation.YOUCANDECIDE => operation
        #       previously       => previous
        #       currently        => current
        #   inserted => relationship
        #   removed => relationship

        event.operation = ACTION_TRANSLATIONS[old.action]

        if old.modification:
            for inserted in old.modification.inserted.all():
                mirror = get_mirror(inserted.type)
                rel = ModelRelationshipModification(
                    field=get_field(inserted.field),
                    entry=get_entry(inserted.value, mirror),
                    operation=1,
                )
                rel.event = event
                relationship_modifications.append(rel)

            for removed in old.modification.removed.all():
                mirror = get_mirror(removed.type)
                rel = ModelRelationshipModification(
                    field=get_field(removed.field),
                    entry=get_entry(removed.value, mirror),
                    operation=-1,
                )
                rel.event = event
                relationship_modifications.append(rel)

            if old.modification.modification:
                previously = {
                    f.field.id: f
                    for f in old.modification.modification.previously.all()
                }
                for currently in old.modification.modification.currently.all():
                    # skip None string values
                    if currently.value == "None":
                        currently.value = None

                    operation = 0
                    previous = None
                    if currently.field.id not in previously:
                        operation = 1
                    else:
                        previous = previously[currently.field.id].value
                        # previous can be "None" string
                        if previous == "None":
                            operation = 1
                            previous = None
                        if previous is not None and currently.value is None:
                            operation = -1

                    val = ModelValueModification(
                        operation=operation,
                        field=get_field(currently.field),
                        previous=previous,
                        current=currently.value,
                    )
                    val.event = event
                    value_modifications.append(val)

                for removed in set(
                    p.field.id for p in old.modification.modification.previously.all()
                ).difference(
                    c.field.id for c in old.modification.modification.currently.all()
                ):
                    removed = previously[removed]
                    # skip None string values
                    if removed.value == "None":
                        continue

                    val = ModelValueModification(
                        operation=-1,
                        field=get_field(removed.field),
                        previous=removed.value,
                        current=None,
                    )
                    val.event = event
                    value_modifications.append(val)

        event.user = old.user
        events.append(event)
        if idx % progress == 0:
            logger.info(f"{(idx // progress) * 10}%...")
        idx += 1

    logger.info("Bulk Saving Converted Objects (This can take a while)")
    Application.objects.using(alias).bulk_create(applications)
    RequestEvent.objects.using(alias).bulk_create(requests)
    UnspecifiedEvent.objects.using(alias).bulk_create(unspecified)
    logger.info("Saved Application, RequestEvent and UnspecifiedEvent")

    ModelMirror.objects.using(alias).bulk_create(mirrors)
    ModelEntry.objects.using(alias).bulk_create(entries)
    ModelField.objects.using(alias).bulk_create(fields)
    logger.info("Saved ModelMirror, ModelEntry, ModelField")

    ModelEvent.objects.using(alias).bulk_create(events)

    ModelValueModification.objects.using(alias).bulk_create(value_modifications)
    ModelRelationshipModification.objects.using(alias).bulk_create(
        relationship_modifications
    )

    logger.info(
        "Saved ModelValueModification, ModelRelationshipModification and ModelEvent"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("automated_logging", "0015_auto_20181229_2323"),
    ]

    operations = [
        # migrations.CreateModel(
        #     # create temporary model
        #     # will be renamed
        #     name='ApplicationTemp',
        #     fields=[
        #         (
        #             'id',
        #             models.UUIDField(
        #                 db_index=True,
        #                 default=uuid.uuid4,
        #                 primary_key=True,
        #                 serialize=False,
        #             ),
        #         ),
        #         ('created_at', models.DateTimeField(auto_now_add=True)),
        #         ('updated_at', models.DateTimeField(auto_now=True)),
        #         ('name', models.CharField(max_length=255, null=True)),
        #     ],
        #     options={
        #         'verbose_name': 'Application',
        #         'verbose_name_plural': 'Applications',
        #     },
        # ),
        migrations.CreateModel(
            name="ModelEntry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("value", models.TextField()),
                ("primary_key", models.TextField()),
            ],
            options={
                "verbose_name": "Model Entry",
                "verbose_name_plural": "Model Entries",
            },
        ),
        migrations.CreateModel(
            name="ModelEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "operation",
                    models.SmallIntegerField(
                        choices=[(1, "create"), (0, "modify"), (-1, "delete")],
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(1),
                        ],
                    ),
                ),
                (
                    "snapshot",
                    picklefield.fields.PickledObjectField(editable=False, null=True),
                ),
                ("performance", models.DurationField(null=True)),
                (
                    "entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.ModelEntry",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Model Event",
                "verbose_name_plural": "Model Events",
            },
        ),
        migrations.CreateModel(
            name="ModelField",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("type", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Model Field",
                "verbose_name_plural": "Model Fields",
            },
        ),
        migrations.CreateModel(
            name="RequestContext",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "content",
                    picklefield.fields.PickledObjectField(editable=False, null=True),
                ),
                ("type", models.CharField(max_length=255)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UnspecifiedEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("message", models.TextField(null=True)),
                ("level", models.PositiveIntegerField(default=20)),
                ("line", models.PositiveIntegerField(null=True)),
                ("file", models.TextField(null=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.Application",
                    ),
                ),
            ],
            options={
                "verbose_name": "Unspecified Event",
                "verbose_name_plural": "Unspecified Events",
            },
        ),
        migrations.CreateModel(
            name="RequestEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("uri", models.TextField()),
                ("status", models.PositiveSmallIntegerField()),
                ("method", models.CharField(max_length=32)),
                ("ip", models.GenericIPAddressField(null=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.Application",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="request_context",
                        to="automated_logging.RequestContext",
                    ),
                ),
                (
                    "response",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="response_context",
                        to="automated_logging.RequestContext",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Request Event",
                "verbose_name_plural": "Request Events",
            },
        ),
        migrations.CreateModel(
            name="ModelValueModification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "operation",
                    models.SmallIntegerField(
                        choices=[(1, "create"), (0, "modify"), (-1, "delete")],
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(1),
                        ],
                    ),
                ),
                ("previous", models.TextField(null=True)),
                ("current", models.TextField(null=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="modifications",
                        to="automated_logging.ModelEvent",
                    ),
                ),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.ModelField",
                    ),
                ),
            ],
            options={
                "verbose_name": "Model Entry Event Value Modification",
                "verbose_name_plural": "Model Entry Event Value Modifications",
            },
        ),
        migrations.CreateModel(
            name="ModelRelationshipModification",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "operation",
                    models.SmallIntegerField(
                        choices=[(1, "create"), (0, "modify"), (-1, "delete")],
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-1),
                            django.core.validators.MaxValueValidator(1),
                        ],
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="relationships",
                        to="automated_logging.ModelEvent",
                    ),
                ),
                (
                    "field",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.ModelField",
                    ),
                ),
                (
                    "entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.ModelEntry",
                    ),
                ),
            ],
            options={
                "verbose_name": "Model Entry Event Relationship Modification",
                "verbose_name_plural": "Model Entry Event Relationship Modifications",
            },
        ),
        migrations.CreateModel(
            name="ModelMirror",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="automated_logging.Application",
                    ),
                ),
            ],
            options={
                "verbose_name": "Model Mirror",
                "verbose_name_plural": "Model Mirrors",
            },
        ),
        migrations.AddField(
            model_name="modelfield",
            name="mirror",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="automated_logging.ModelMirror",
            ),
        ),
        migrations.AddField(
            model_name="modelentry",
            name="mirror",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="automated_logging.ModelMirror",
            ),
        ),
        migrations.AlterField(
            model_name="application",
            name="name",
            field=models.CharField(max_length=255, null=True),
        ),
        # end of adding
        # conversion
        migrations.RunPython(convert),
        # migrations.RenameModel('ApplicationTemp', 'Application'),
        # removing 5.x.x
        migrations.RemoveField(
            model_name="field",
            name="model",
        ),
        migrations.RemoveField(
            model_name="model",
            name="application",
        ),
        migrations.RemoveField(
            model_name="model",
            name="information",
        ),
        migrations.RemoveField(
            model_name="model",
            name="modification",
        ),
        migrations.RemoveField(
            model_name="model",
            name="user",
        ),
        migrations.RemoveField(
            model_name="modelchangelog",
            name="information",
        ),
        migrations.RemoveField(
            model_name="modelchangelog",
            name="inserted",
        ),
        migrations.RemoveField(
            model_name="modelchangelog",
            name="modification",
        ),
        migrations.RemoveField(
            model_name="modelchangelog",
            name="removed",
        ),
        migrations.RemoveField(
            model_name="modelmodification",
            name="currently",
        ),
        migrations.RemoveField(
            model_name="modelmodification",
            name="previously",
        ),
        migrations.RemoveField(
            model_name="modelobject",
            name="field",
        ),
        migrations.RemoveField(
            model_name="modelobject",
            name="type",
        ),
        migrations.RemoveField(
            model_name="request",
            name="application",
        ),
        migrations.RemoveField(
            model_name="request",
            name="user",
        ),
        migrations.DeleteModel(
            name="Unspecified",
        ),
        # migrations.DeleteModel(name='Application',),
        migrations.DeleteModel(
            name="Field",
        ),
        migrations.DeleteModel(
            name="Model",
        ),
        migrations.DeleteModel(
            name="ModelChangelog",
        ),
        migrations.DeleteModel(
            name="ModelModification",
        ),
        migrations.DeleteModel(
            name="ModelObject",
        ),
        migrations.DeleteModel(
            name="Request",
        ),
        # end of removing
    ]
