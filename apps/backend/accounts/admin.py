from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, User


@admin.register(User)
class NovaUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("بيانات العميل", {"fields": ("phone", "city", "address")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("بيانات العميل", {"fields": ("email", "phone", "city", "address")}),
    )
    list_display = ("username", "email", "phone", "is_staff", "is_active")
    search_fields = ("username", "email", "phone")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("label", "full_name", "user", "city", "country_code", "is_default")
    list_filter = ("country_code", "city", "is_default")
    search_fields = ("full_name", "phone", "user__email", "line1")
