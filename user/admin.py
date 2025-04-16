from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,FollowInfo

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('uuid','email', 'phone_number', 'nickname', 'token_user', 'created_at', 'updated_at', 'is_staff', 'is_superuser', 'is_active')
    
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'phone_number', 'nickname')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone_number', 'nickname')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'nickname', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    # Token_user maydonini faqat ko'rsatish, lekin tahrirlanmasin
    readonly_fields = ('created_at', 'updated_at', 'token_user')

    filter_horizontal = ()
    list_per_page = 20

# CustomUser modelini admin paneliga qo'shish
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(FollowInfo)
class FollowInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'subscriber_count', 'subscription_count')
    search_fields = ('user__phone_number', 'user__email')
    readonly_fields = ('created_at', 'subscriber_count', 'subscription_count')
    
    def subscriber_count(self, obj):
        return len(obj.podpischik)
    subscriber_count.short_description = 'Podpischik soni'

    def subscription_count(self, obj):
        return len(obj.podpiski)
    subscription_count.short_description = 'Podpiski soni'