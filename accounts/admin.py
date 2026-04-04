from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User, AuditLog

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'supabase_uid')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Auth', {'fields': ('role', 'supabase_uid')}),
    )
    search_fields = ('username', 'email', 'supabase_uid')

# Ensure Group is managed in admin (User's request)
admin.site.unregister(Group)
admin.site.register(Group)

admin.site.register(User, CustomUserAdmin)
admin.site.register(AuditLog)
