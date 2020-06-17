"""
File handles every signal related to the saving/deletion of django models.
"""
import logging
from collections import namedtuple
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from automated_logging.middleware import AutomatedLoggingMiddleware
from automated_logging.models import (
    ModelValueModification,
    ModelField,
    ModelMirror,
)
from automated_logging.settings import settings
from automated_logging.signals import model_exclusion


ChangeSet = namedtuple('ChangeSet', ('deleted', 'added', 'changed'))
logger = logging.getLogger(__name__)


@receiver(pre_save, weak=False)
@transaction.atomic
def pre_save_signal(sender, instance, **kwargs) -> None:
    """
    Compares the current instance and old instance (fetched via the pk)
    and generates a dictionary of changes

    TODO: consider moving this code somewhere different

    :param sender:
    :param instance:
    :param kwargs:
    :return: None
    """
    # clear the _dal_event to be sure
    instance._dal_event = None

    excluded = model_exclusion(instance)
    instance._dal_excluded = excluded
    if excluded:
        return

    try:
        pre = sender.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        return

    old, new = pre.__dict__, instance.__dict__

    previously = set(
        k for k in old.keys() if not k.startswith('_') and old[k] is not None
    )
    currently = set(
        k for k in new.keys() if not k.startswith('_') and new[k] is not None
    )

    added = currently.difference(previously)
    deleted = previously.difference(currently)
    changed = (
        set(
            k
            for k, v in set(
                # generate a set from the dict of old values
                # exclude protected and magic attributes
                (k, v)
                for k, v in old.items()
                if not k.startswith('_')
            ).difference(
                set(
                    # generate a set from the dict of new values
                    # also exclude the protected and magic attributes
                    (k, v)
                    for k, v in new.items()
                    if not k.startswith('_')
                )
            )
            # the difference between the two sets
            # because the keys are the same, but values are different
            # will result in a change set of changed values
            # ('a', 'b') in old and new will get eliminated
            # ('a', 'b') in old and ('a', 'c') in new will
            # result in ('a', 'b') in the new set as that is
            # different.
        )
        # remove all added and deleted attributes from the changelist
        # they would still be present, because None -> Value
        .difference(added).difference(deleted)
    )

    modifications = []

    summary = [
        *({'operation': 1, 'previous': None, 'current': new[k]} for k in added),
        *({'operation': -1, 'previous': old[k], 'current': None} for k in deleted),
        *({'operation': 0, 'previous': old[k], 'current': new[k]} for k in changed),
    ]

    model = ModelMirror()
    model.name = sender.__name__
    model.application = instance._meta.app_label

    for entry in summary:
        field = ModelField()
        field.name = entry
        field.model = model
        field.type = repr(getattr(sender, entry))
        # field.content_type =

        modification = ModelValueModification()
        modification.operation = entry['operation']
        modification.field = field
        modification.previous = repr(entry['previous'])
        modification.current = repr(entry['current'])

        modifications.append(modification)

    instance._dal_modifications = modifications
    if settings.model.performance:
        instance._dal_performance = datetime.now()


def post_processor(status, sender, instance, updated=None, suffix='') -> None:
    """
    Due to the fact that both post_delete and post_save have
    the same logic for propagating changes, we have this helper class
    to do so, just simply wraps and logs the data the handler needs.

    :param status: create, modify, delete
    :param sender: model class
    :param instance: model instance
    :param updated: updated fields
    :param suffix: suffix to be added to the message
    :return: None
    """
    past = {'modify': 'modified', 'create': 'created', 'delete': 'deleted'}

    user = AutomatedLoggingMiddleware.get_current_user()
    application = instance._meta.app_label
    model = sender.__name__

    logger.log(
        settings.model.loglevel,
        f'{user} {past[status]} [{application}][{model}]{instance}{suffix}',
        extra={
            'action': 'model',
            'data': {
                'status': status,
                'user': user,
                'instance': instance,
                'sender': sender,
                'modifications': hasattr(instance, '_dal_modifications')
                and instance._dal_modifications,
                'updated': updated,
            },
        },
    )


@receiver(post_save, weak=False)
@transaction.atomic
def post_save_signal(sender, instance, created, update_fields, **kwargs) -> None:
    """
    Signal is getting called after a save has been concluded. When this
    is the case we can be sure the save was successful and then only
    propagate the changes to the handler.

    :param sender: model class
    :param instance: model instance
    :param created: bool, was the model created?
    :param update_fields: which fields got explicitly updated?
    :param kwargs: django needs kwargs to be there
    :return: -
    """
    lazy = hasattr(instance, '_dal_excluded')
    if lazy and instance._dal_excluded:
        return
    elif not lazy and model_exclusion(instance):
        return

    status = 'create' if created else 'modify'
    suffix = f''
    if (
        status == 'modify'
        and hasattr(instance, '_dal_modifications')
        and settings.model.detailed_message
    ):
        suffix = f' Changelog: {instance._dal_modifications}'

    post_processor(status, sender, instance, update_fields, suffix)


@receiver(post_delete, weak=False)
@transaction.atomic
def post_delete_signal(sender, instance, **kwargs) -> None:
    """
    Signal is getting called after instance deletion. We just redirect the
    event to the post_processor.

    :param sender: model class
    :param instance: model instance
    :param kwargs: required bt django
    :return: -
    """
    post_processor('delete', sender, instance)
