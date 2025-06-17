from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser,Purpose,UserImage,UserProfile,Interest,UserProfileExtension

@admin.register(UserProfileExtension)
class UserProfileExtensionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'requests_left', 'daily_requests_limit', 'last_reset')
    list_filter = ('last_reset',)
    search_fields = ('user_profile__user__email', 'user_profile__user__phone')
    filter_horizontal = ('subscribers', 'requests', 'blocked_users')

    def user_email(self, obj):
        return obj.user_profile.user.email
    user_email.short_description = "User Email"


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

@admin.register(Purpose)
class PurposeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'birth_year', 'gender', 'region', 'district')
    filter_horizontal = ('purposes', 'interests')

@admin.register(UserImage)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'is_main', 'is_auth')


@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    ordering = ['-created_at']
    list_display = ('email', 'name', 'phone', 'is_active', 'is_staff')
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
