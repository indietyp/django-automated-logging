from django.contrib import admin
from . import models


class ReadOnlyAdminMixin(admin.ModelAdmin):
    """Disables all editing capabilities."""

    change_form_template = "admin/view.html"

    def __init__(self, *args, **kwargs):
        super(ReadOnlyAdminMixin, self).__init__(*args, **kwargs)
        self.readonly_fields = [f.name for f in self.model._meta.get_fields()]

    def get_actions(self, request):
        actions = super(ReadOnlyAdminMixin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


class ModelAdmin(ReadOnlyAdminMixin):
    def get_prev(self, obj):
        if obj.modification is not None and obj.modification.modification is not None:
            return ", ".join(str(v) for v in obj.modification.modification.previously.all())
        else:
            return ''
    get_prev.short_description = 'Previous Value'

    def get_curr(self, obj):
        if obj.modification is not None and obj.modification.modification is not None:
            return ", ".join(str(v) for v in obj.modification.modification.currently.all())
        else:
            return ''
    get_curr.short_description = 'Changed Value'

    def get_remo(self, obj):
        if obj.modification is not None and obj.modification.removed is not None:
            return ", ".join(str(v) for v in obj.modification.removed.all())
        else:
            return ''
    get_remo.short_description = 'Removed'

    def get_inser(self, obj):
        if obj.modification is not None and obj.modification.inserted is not None:
            return ", ".join(str(v) for v in obj.modification.inserted.all())
        else:
            return ''
    get_inser.short_description = 'Inserted'

    def get_infor(self, obj):
        if obj.information is not None and obj.information.type is not None:
            return obj.information.type.model + '.' + str(obj.application)
        else:
            return ''
    get_infor.short_description = 'Object'

    list_display = (
        'user',
        'action',
        'get_prev',
        'get_curr',
        'get_remo',
        'get_inser',
        'get_infor',
        'updated_at',
    )

    list_filter = (
        'updated_at',
        'user',
    )

    date_hierarchy = 'updated_at'
    ordering = ('-updated_at',)


class RequestAdmin(ReadOnlyAdminMixin):

    list_display = (
        'user',
        'method',
        'uri',
        'application',
        'updated_at'
    )
    list_filter = ('updated_at', 'application', 'user')
    date_hierarchy = 'updated_at'
    ordering = ('-updated_at',)


class UnspecifiedAdmin(ReadOnlyAdminMixin):

    list_display = (
        'level',
        'file',
        'line',
        'message',
        'updated_at'
    )
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)


# class LDAPAdmin(ReadOnlyAdminMixin):

#     list_display = (
#         'action',
#         'succeeded',
#         'errorMessage',
#         'basedn',
#         'entry',
#         'objectClass',
#         'cn',
#         'existing_members',
#         'data_members',
#         'diff_members',
#     )
#     list_filter = ('created_at', 'updated_at')
#     date_hierarchy = 'created_at'


def _register(model, admin_class):
    admin.site.register(model, admin_class)


_register(models.Model, ModelAdmin)
_register(models.Request, RequestAdmin)
_register(models.Unspecified, UnspecifiedAdmin)
# _register(models.LDAP, LDAPAdmin)
