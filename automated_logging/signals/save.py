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
    Application,
    ModelEvent,
    ModelEntry,
)
from automated_logging.settings import settings
from automated_logging.signals import (
    model_exclusion,
    lazy_model_exclusion,
    field_exclusion,
)
from automated_logging.helpers import (
    get_or_create_meta,
    Operation,
    get_or_create_model_event,
)

ChangeSet = namedtuple('ChangeSet', ('deleted', 'added', 'changed'))
logger = logging.getLogger(__name__)


@receiver(pre_save, weak=False)
@transaction.atomic
def pre_save_signal(sender, instance, **kwargs) -> None:
    """
    Compares the current instance and old instance (fetched via the pk)
    and generates a dictionary of changes

    :param sender:
    :param instance:
    :param kwargs:
    :return: None
    """
    get_or_create_meta(instance)
    # clear the event to be sure
    instance._meta.dal.event = None

    operation = Operation.MODIFY
    try:
        pre = sender.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        # we need to postpone the return to evaluate model exclusion
        operation = Operation.CREATE

    excluded = model_exclusion(instance, operation, instance.__class__)
    instance._meta.dal.excluded = excluded
    if excluded:
        return

    if operation == Operation.CREATE:
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

    summary = [
        *(
            {
                'operation': Operation.CREATE,
                'previous': None,
                'current': new[k],
                'key': k,
            }
            for k in added
        ),
        *(
            {
                'operation': Operation.DELETE,
                'previous': old[k],
                'current': None,
                'key': k,
            }
            for k in deleted
        ),
        *(
            {
                'operation': Operation.MODIFY,
                'previous': old[k],
                'current': new[k],
                'key': k,
            }
            for k in changed
        ),
    ]

    # field exclusion
    summary = [s for s in summary if not field_exclusion(s['key'], instance)]

    model = ModelMirror()
    model.name = sender.__name__
    model.application = Application(name=instance._meta.app_label)

    modifications = []
    for entry in summary:
        field = ModelField()
        field.name = entry['key']
        field.model = model
        field.type = repr(getattr(sender, entry['key']))

        modification = ModelValueModification()
        modification.operation = entry['operation']
        modification.field = field
        modification.previous = repr(entry['previous'])
        modification.current = repr(entry['current'])

        modifications.append(modification)

    instance._meta.dal.modifications = modifications

    if settings.model.performance:
        instance._meta.dal.performance = datetime.now()


def post_processor(status, sender, instance, updated=None, suffix='') -> None:
    """
    Due to the fact that both post_delete and post_save have
    the same logic for propagating changes, we have this helper class
    to do so, just simply wraps and logs the data the handler needs.

    The event gets created here instead of the handler to keep
    everything consistent and have the handler as simple as possible.

    :param status: create, modify, delete
    :param sender: model class
    :param instance: model instance
    :param updated: updated fields
    :param suffix: suffix to be added to the message
    :return: None
    """
    past = {'modify': 'modified', 'create': 'created', 'delete': 'deleted'}

    get_or_create_meta(instance)
    if settings.model.performance and hasattr(instance._meta.dal, 'performance'):
        instance._meta.dal.performance = datetime.now() - instance._meta.dal.performance

    event, _ = get_or_create_model_event(instance, force=True, extra=True)

    logger.log(
        settings.model.loglevel,
        f'{event.user or "Anonymous"} {past[status]} '
        f'{event.model.model.application}.{sender.__name__} | '
        f'Instance: {instance!r}{suffix}',
        extra={
            'action': 'model',
            'data': {'status': status, 'instance': instance},
            'event': event,
            'modifications': getattr(instance._meta.dal, 'modifications', None),
        },
    )


@receiver(post_save, weak=False)
@transaction.atomic
def post_save_signal(
    sender, instance, created, update_fields: frozenset, **kwargs
) -> None:
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
    status = 'create' if created else 'modify'
    if lazy_model_exclusion(
        instance,
        Operation.CREATE if status == 'create' else Operation.MODIFY,
        instance.__class__,
    ):
        return
    get_or_create_meta(instance)

    suffix = f''
    if (
        status == 'modify'
        and hasattr(instance._meta.dal, 'modifications')
        and settings.model.detailed_message
    ):
        suffix = (
            f' | Modifications: '
            f'{", ".join([m.short() for m in instance._meta.dal.modifications])}'
        )

    if update_fields is not None and hasattr(instance._meta.dal, 'modifications'):
        instance._meta.dal.modifications = [
            m for m in instance._meta.dal.modifications if m.field.name in update_fields
        ]

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
    if lazy_model_exclusion(instance, Operation.DELETE, instance.__class__):
        return

    post_processor('delete', sender, instance)
