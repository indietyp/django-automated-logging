"""This file handles everything related to saving and deleting model objects."""
import re
import logging

from .. import settings
from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.db.models.signals import post_save, pre_save

from ..models import ModelChangelog, ModelModification, ModelObject, Field
from django.contrib.contenttypes.models import ContentType
from . import validate_instance, processor


@receiver(pre_save, weak=False)
@transaction.atomic
def comparison_callback(sender, instance, **kwargs):
    """Comparing old and new object to determin which fields changed how"""
    if validate_instance(instance) and settings.AUTOMATED_LOGGING['to_database']:
        try:
            old = sender.objects.get(pk=instance.pk)
        except Exception:
            return None

        try:
            mdl = ContentType.objects.get_for_model(instance)
            cur, ins = old.__dict__, instance.__dict__
            old, new = {}, {}
            for k in cur.keys():
                # _ fields are not real model fields, only state or cache fields
                # getting filtered
                if re.match('(_)(.*?)', k):
                    continue

                changed = False
                if k in ins.keys():
                    if cur[k] != ins[k]:
                        changed = True
                        new[k] = ModelObject()
                        new[k].value = str(ins[k])
                        new[k].save()

                        try:
                            new[k].type = ContentType.objects.get_for_model(ins[k])
                        except Exception:
                            logger = logging.getLogger(__name__)
                            logger.debug('Could not dermin the content type of the field')

                        new[k].field = Field.objects.get_or_create(name=k, model=mdl)[0]
                        new[k].save()
                else:
                    changed = True

                if changed:
                    old[k] = ModelObject()
                    old[k].value = str(cur[k])
                    old[k].save()

                    try:
                        old[k].type = ContentType.objects.get_for_model(cur[k])
                    except Exception:
                        logger = logging.getLogger(__name__)
                        logger.debug('Could not dermin the content type of the field')

                    old[k].field = Field.objects.get_or_create(name=k, model=mdl)[0]
                    old[k].save()

            if old or new:
                changelog = ModelChangelog()
                changelog.save()

                changelog.modification = ModelModification()
                changelog.modification.save()
                changelog.modification.previously.add(*old.values())
                changelog.modification.currently.add(*new.values())

                changelog.information = ModelObject()
                changelog.information.save()
                changelog.information.value = repr(instance)
                changelog.information.type = ContentType.objects.get_for_model(instance)
                changelog.information.save()
                changelog.save()

                instance.al_chl = changelog

                return instance

        except Exception as e:
            print(e)
            logger = logging.getLogger(__name__)
            logger.warning('automated_logging recorded an exception that should not have happended')


@receiver(post_save, weak=False)
@transaction.atomic
def save_callback(sender, instance, created, update_fields, **kwargs):
    """Save object & link logging entry"""
    if validate_instance(instance):
        status = 'add' if created is True else 'change'
        change = ''

        if status == 'change' and 'al_chl' in instance.__dict__.keys():
            changelog = instance.al_chl.modification
            change = ' to following changed: {}'.format(changelog)

        processor(status, sender, instance, update_fields, addition=change)


@receiver(post_delete, weak=False)
@transaction.atomic
def delete_callback(sender, instance, **kwargs):
    """Triggered when deleted -> logged"""
    status = 'delete'
    processor(status, sender, instance)
