from django.contrib.admin import (
    ModelAdmin,
    RelatedOnlyFieldListFilter,
    TabularInline,
)
from django.contrib.admin.options import BaseModelAdmin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin import register
from django.shortcuts import resolve_url
from django.utils.html import format_html
from django.utils.safestring import SafeText

from automated_logging.helpers import Operation
from automated_logging.models import (
    ModelEvent,
    ModelValueModification,
    ModelRelationshipModification,
    ModelEntry,
    BaseModel,
)


class MixinBase(BaseModelAdmin):
    """
    TabularInline and ModelAdmin readonly mixin have both the same methods and
    return the same, because of that fact we have a mixin base
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.readonly_fields = [f.name for f in self.model._meta.get_fields()]

    def get_actions(self, request):
        """ get_actions from ModelAdmin, but remove all write operations."""
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)

        return actions

    def has_add_permission(self, request, instance=None):
        """ no-one should have the ability to add something => r/o"""
        return False

    def has_delete_permission(self, request, instance=None):
        """ no-one should have the ability to delete something => r/o """
        return False

    def has_change_permission(self, request, instance=None):
        """ no-one should have the ability to edit something => r/o """
        return False

    def save_model(self, request, instance, form, change):
        """ disable saving by doing nothing """
        pass

    def delete_model(self, request, instance):
        """ disable deleting by doing nothing """
        pass

    def save_related(self, request, form, formsets, change):
        """ we don't need to save related, because save_model does nothing """
        pass

    # helpers
    def model_admin_url(self, instance: BaseModel, name: str = None) -> str:
        """ Helper to return a URL to another object """
        url = resolve_url(
            admin_urlname(instance._meta, SafeText("change")), instance.pk
        )
        return format_html('<a href="{}">{}</a>', url, name or str(instance))


class ReadOnlyAdminMixin(MixinBase, ModelAdmin):
    """ Disables all editing capabilities for the model admin """

    change_form_template = "dal/admin/view.html"


class ReadOnlyTabularInlineMixing(MixinBase, TabularInline):
    """ Disables all editing capabilities for inline """

    model = None


class ModelValueModificationInline(ReadOnlyTabularInlineMixing):
    """ inline for all modifications """

    model = ModelValueModification

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.readonly_fields = [*self.readonly_fields, 'get_uuid', 'get_field']

    def get_uuid(self, instance):
        """ make the uuid small """
        return str(instance.id).split('-')[0]

    get_uuid.short_description = 'UUID'

    def get_field(self, instance):
        """ show the field name """
        return instance.field.name

    get_field.short_description = 'Field'

    fields = ('get_uuid', 'operation', 'get_field', 'previous', 'current')
    can_delete = False

    verbose_name = 'Modification'
    verbose_name_plural = 'Modifications'


class ModelRelationshipModificationInline(ReadOnlyTabularInlineMixing):
    """ inline for all relationship modifications """

    model = ModelRelationshipModification

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.readonly_fields = [*self.readonly_fields, 'get_uuid', 'get_field']

    def get_uuid(self, instance):
        """ make the uuid small """
        return str(instance.id).split('-')[0]

    get_uuid.short_description = 'UUID'

    def get_field(self, instance):
        """ show the field name """
        return instance.field.name

    get_field.short_description = 'Field'

    fields = ('get_uuid', 'operation', 'get_field', 'model')
    can_delete = False

    verbose_name = 'Relationship'
    verbose_name_plural = 'Relationships'


@register(ModelEvent)
class ModelEventAdmin(ReadOnlyAdminMixin):
    """ admin page specification """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.readonly_fields = [
            *self.readonly_fields,
            'get_application',
            'get_user',
            'get_model_link',
        ]

    def get_modifications(self, instance):
        """
        Modifications in short form, are colored for better readability.

        Colors taken from
        https://github.com/django/django/tree/master/django/contrib/admin/static/admin/img
        """
        colors = {
            Operation.CREATE: '#70bf2b',
            Operation.MODIFY: '#efb80b',
            Operation.DELETE: '#dd4646',
        }
        return format_html(
            ', '.join(
                [
                    *[
                        f'<span style="color: {colors[Operation(m.operation)]};">'
                        f'{m.short()}'
                        f'</span>'
                        for m in instance.modifications.all()
                    ],
                    *[
                        f'<span style="color: {colors[Operation(r.operation)]};">'
                        f'{r.medium()[0]}'
                        f'</span>[{r.medium()[1]}]'
                        for r in instance.relationships.all()
                    ],
                ],
            )
        )

    get_modifications.short_description = 'Modifications'

    def get_model(self, instance):
        """
        get the model
        TODO: consider splitting this up to model/pk/value
        """
        return instance.model.short()

    get_model.short_description = 'Model'

    def get_model_link(self, instance):
        """ get the model with a link to the entry """
        return self.model_admin_url(instance.model)

    get_model_link.short_description = 'Model'

    def get_application(self, instance):
        """
        helper to get the application from the child ModelMirror
        :param instance:
        :return:
        """
        return instance.model.model.application

    get_application.short_description = 'Application'

    def get_id(self, instance):
        """ shorten the id to the first 8 digits """
        return str(instance.id).split('-')[0]

    def get_user(self, instance):
        """ return the user with a link """
        return self.model_admin_url(instance.user) if instance.user else None

    get_id.short_description = 'UUID'

    list_display = (
        'get_id',
        'get_user',
        'get_application',
        'get_model',
        'get_modifications',
    )

    # form = ModelEventForm
    list_filter = ('updated_at', ('user', RelatedOnlyFieldListFilter))

    date_hierarchy = 'updated_at'
    ordering = ('-updated_at',)

    fieldsets = (
        (
            'General',
            {'fields': ('id', 'get_user', 'get_application', 'get_model_link')},
        ),
        ('Additional Information', {'fields': ('performance', 'snapshot')}),
    )
    inlines = [ModelValueModificationInline, ModelRelationshipModificationInline]

    show_change_link = True


@register(ModelEntry)
class ModelEntryAdmin(ReadOnlyAdminMixin):
    """ admin page for a single entry """

    def has_module_permission(self, request):
        """ remove model entries from the index.html list """
        return False

    fieldsets = (('General', {'fields': ('id',)},),)
