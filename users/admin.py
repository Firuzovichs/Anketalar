from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser,
    Purpose,
    UserImage,
    UserProfile,
    Interest,
    UserProfileExtension,
    Region,
    District,
    PendingUser
)


@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'phone', 'code', 'code_expires', 'created_at','is_verified')
    list_filter = ('created_at',)
    search_fields = ('email', 'phone', 'code')
    readonly_fields = ('created_at',)

    fieldsets = (
        ("User Contact", {
            "fields": ("email", "phone"),
        }),
        ("Verification", {
            "fields": ("code", "code_expires"),
        }),
        ("System Info", {
            "fields": ("created_at",),
        }),
    )


# --- REGION ADMIN ---
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 25


# --- DISTRICT ADMIN ---
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'region')
    list_filter = ('region',)
    search_fields = ('name', 'region__name')
    ordering = ('region', 'name')
    list_per_page = 25


# --- USER PROFILE EXTENSION ---
@admin.register(UserProfileExtension)
class UserProfileExtensionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'requests_left', 'daily_requests_limit', 'last_reset')
    list_filter = ('last_reset',)
    search_fields = ('user_profile__user__email', 'user_profile__user__phone')
    filter_horizontal = ('subscribers', 'requests', 'blocked_users')
    readonly_fields = ('last_reset',)

    def user_email(self, obj):
        return obj.user_profile.user.email
    user_email.short_description = "User Email"


# --- INTEREST ADMIN ---
@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)
    ordering = ('title',)


# --- PURPOSE ADMIN ---
@admin.register(Purpose)
class PurposeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)
    ordering = ('title',)


# --- USER PROFILE ADMIN ---
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'birth_year', 'gender', 'region', 'district')
    list_filter = ('gender', 'region', 'district')
    search_fields = ('user__email', 'user__name', 'region__name', 'district__name')
    filter_horizontal = ('purposes', 'interests')
    ordering = ('user',)
    list_per_page = 25


# --- USER IMAGE ADMIN ---
@admin.register(UserImage)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'is_main', 'is_auth')
    list_filter = ('is_main', 'is_auth')
    search_fields = ('user_profile__user__email',)


# --- CUSTOM USER ADMIN ---
@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    ordering = ['-created_at']
    list_display = ('email', 'name', 'phone', 'is_active', 'is_staff')
    list_display_links = ('email', 'phone')
    list_filter = ('is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'phone', 'name', 'uuid')
    readonly_fields = ('created_at', 'updated_at', 'uuid', 'token')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'phone')}),
        (_('Token info'), {'fields': ('uuid', 'token')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'name', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
