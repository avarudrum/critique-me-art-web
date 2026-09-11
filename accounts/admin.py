from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('bio', 'primary_medium')}),
    )
    list_display = ('username', 'email', 'primary_medium', 'is_staff')


admin.site.register(User, CustomUserAdmin)