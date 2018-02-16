from django.contrib import admin
from .models import *


# class LDAPEventLogEntryAdmin(AbstractViewOnlyAdmin):
#     list_display = ('date_created',
#                     'action',
#                     'succeeded',
#                     'errorMessage',
#                     'basedn',
#                     'entry',
#                     'cn'
#                     )

#     # list_filter = ['action', 'succeeded', 'errorMessage', 'basedn', 'cn', 'date_created']

#     search_fields = ['action',
#                      'errorMessage',
#                      'basedn',
#                      'entry',
#                      'cn',
#                      'existing_members',
#                      'data_members']


# class GlobalRequestEventEntryAdmin(AbstractViewOnlyAdmin):
#     list_display = ('date_created',
#                     'application',
#                     'user',
#                     'request'
#                     )

#     list_filter = ['application', 'user']


# class GlobalModelEventEntryAdmin(AbstractViewOnlyAdmin):
#     list_display = ('date_created',
#                     'application',
#                     'user',
#                     'mode',
#                     'object_id',
#                     'object_name',
#                     'object_model',
#                     'modified_fields')

#     list_filter = ['application', 'mode', 'object_name', 'object_model', 'user']

#     search_fields = ['application',
#                      'mode',
#                      'user__lastname',
#                      'user__username',
#                      'user__firstname',
#                      'object_name',
#                      'object_id',
#                      'modified_fields__modified_before',
#                      'modified_fields__modified_now',
#                      'modified_fields__removed',
#                      'modified_fields__added'
#                      ]


# class GlobalLoggingEntryAdmin(AbstractViewOnlyAdmin):
#     list_display = ('date_created',
#                     'level',
#                     'line',
#                     'path',
#                     'message'
#                     )

#     list_filter = ['level', 'path']


# class GlobalModelEntryChangeAdmin(AbstractViewOnlyAdmin):
#     list_display = ('date_created',
#                     'modified_before',
#                     'modified_now',
#                     'removed',
#                     'added',
#                     'object_id',
#                     'object_model'
#                     )

#     list_filter = ['object_id', 'object_model']


# admin.site.register(GlobalLdapEventLogEntry, LDAPEventLogEntryAdmin)
# admin.site.register(GlobalRequestEventEntry, GlobalRequestEventEntryAdmin)
# admin.site.register(GlobalModelEventEntry, GlobalModelEventEntryAdmin)
# admin.site.register(GlobalLoggingEntry, GlobalLoggingEntryAdmin)
# admin.site.register(GlobalModelEntryChange, GlobalModelEntryChangeAdmin)
