from django.contrib import admin
from . import models


# class ApplicationAdmin(admin.ModelAdmin):

#     list_display = ('name', )
#     list_filter = ('created_at', 'updated_at')
#     search_fields = ('name',)
#     date_hierarchy = 'created_at'


# class ModelObjectAdmin(admin.ModelAdmin):

#     list_display = ('value', 'type')
#     list_filter = ('created_at', 'updated_at', 'type')
#     date_hierarchy = 'created_at'


# class ModelModificationAdmin(admin.ModelAdmin):

#     list_display = ('id', 'created_at', 'updated_at')
#     list_filter = ('created_at', 'updated_at')
#     raw_id_fields = ('previously', 'currently')
#     date_hierarchy = 'created_at'


# class ModelChangelogAdmin(admin.ModelAdmin):

#     list_display = (
#         'modification',
#         'information',
#     )
#     list_filter = ('created_at', 'updated_at', 'modification', 'information')
#     raw_id_fields = ('inserted', 'removed')
#     date_hierarchy = 'created_at'


class ModelAdmin(admin.ModelAdmin):
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


class RequestAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'application',
        'url',
        'updated_at'
    )
    list_filter = ('created_at', 'updated_at', 'application', 'user')
    date_hierarchy = 'created_at'


class UnspecifiedAdmin(admin.ModelAdmin):

    list_display = (
        'level',
        'file',
        'line',
        'message',
        'updated_at'
    )
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


# class LDAPAdmin(admin.ModelAdmin):

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


# _register(models.Application, ApplicationAdmin)
# _register(models.ModelObject, ModelObjectAdmin)
# _register(models.ModelModification, ModelModificationAdmin)
# _register(models.ModelChangelog, ModelChangelogAdmin)
_register(models.Model, ModelAdmin)
_register(models.Request, RequestAdmin)
_register(models.Unspecified, UnspecifiedAdmin)
# _register(models.LDAP, LDAPAdmin)
