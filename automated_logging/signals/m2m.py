"""
This module specifically handlers "many to many" changes, those are
a bit more complicated as we need to detect the changes
on a per field basis.

This finds the changes and redirects them to the handler,
without doing any changes to the database.

TODO: it should really print a message
"""


import logging
from typing import Optional

from django.db.models import ManyToManyField, ManyToManyRel
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from automated_logging.helpers import Operation
from automated_logging.models import (
    ModelRelationshipModification,
    ModelEntry,
    ModelMirror,
    Application,
    ModelField,
)
from automated_logging.settings import settings
from automated_logging.signals import model_exclusion, lazy_model_exclusion

logger = logging.getLogger(__name__)


def find_m2m_rel(sender, model) -> Optional[ManyToManyRel]:
    """
    This finds the "many to many" relationship that is used by the sender.
    """
    for field in model._meta.get_fields():
        if isinstance(field, ManyToManyRel) and field.through == sender:
            return field

    return None


def post_processor(sender, instance, model, operation, targets):
    """
    if the change is in reverse or not, the processing of the changes is still
    the same, so we have this method to take care of constructing the changes
    :param sender:
    :param instance:
    :param model:
    :param operation:
    :param targets:
    :return:
    """
    # TODO: append to instance, should be done in handler
    relationships = []

    m2m_rel = find_m2m_rel(sender, model)
    if not m2m_rel:
        logger.warning(f'[DAL] save[m2m] could not find ManyToManyField for {instance}')
        return

    field = ModelField()
    field.name = m2m_rel.field.name
    field.model = ModelMirror(
        name=model.__name__, application=Application(name=instance._meta.app_label)
    )

    for target in targets:
        relationship = ModelRelationshipModification()
        relationship.operation = operation
        relationship.field = field
        mirror = ModelMirror()
        mirror.name = target.__class__.__name__
        mirror.application = Application(name=target._meta.app_label)
        relationship.model = ModelEntry(
            model=mirror, value=repr(target), primary_key=target.pk
        )
        relationships.append(relationship)

    if len(relationships) == 0:
        # there was no actual change, so we're not propagating the event
        return

    # TODO: construct event

    user = None
    logger.log(
        settings.model.loglevel,
        f'{user or "Anonymous"} modified field '
        f'{field.name} | Model: '
        f'{field.model.application}.{field.model} '
        f'| Modifications: {", ".join([r.short() for r in relationships])}',
        extra={
            'action': 'model[m2m]',
            'data': {
                'relationships': relationships,
                'instance': instance,
                'sender': model,
            },
        },
    )


@receiver(m2m_changed, weak=False)
def m2m_changed_signal(
    sender, instance, action, reverse, model, pk_set, using, **kwargs
) -> None:
    # TODO: pre_clear and post_clear
    if action not in ['post_add', 'post_remove', 'pre_clear']:
        return

    if action in ['post_add']:
        operation = Operation.CREATE
    else:
        operation = Operation.DELETE

    # if reverse targets should log the removal of the specific instance
    # if not reverse do it on the current one

    targets = model.objects.filter(pk__in=list(pk_set))
    if reverse:
        for target in [
            t for t in targets if not lazy_model_exclusion(t, operation, t.__class__)
        ]:
            post_processor(sender, target, target.__class__, operation, [instance])
    else:
        if lazy_model_exclusion(instance, operation, instance.__class__):
            return

        post_processor(sender, instance, model, operation, targets)
