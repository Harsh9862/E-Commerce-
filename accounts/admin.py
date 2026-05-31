from django.contrib import admin
from .models import Account, Profile
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email','first_name','last_name','username','last_login','date_joined','is_active')
    list_display_links = ('email','first_name','last_name')
    readonly_fields = ('last_login','date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(Account,AccountAdmin)    # As we have created new way of login in admin panal so for that first we have to delete the old data i.e. old db and migration files


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'company', 'country', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


admin.site.register(Profile, ProfileAdmin)
