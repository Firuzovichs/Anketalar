import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import secrets
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        
        user = self.model(
            phone_number=phone_number,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(phone_number, email, password, **extra_fields)

def generate_token():
    return secrets.token_hex(16)

class CustomUser(AbstractBaseUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    token_user = models.CharField(max_length=32, unique=True, editable=False, default=generate_token)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Ensuring that 'is_superuser' field exists

    USERNAME_FIELD = 'phone_number'  # Login field
    REQUIRED_FIELDS = ['email']  # Other required fields for the superuser creation

    objects = CustomUserManager()

    class Meta:
        db_table = 'custom_user'
        indexes = [
            models.Index(fields=['uuid']),
            models.Index(fields=['token_user']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.phone_number
    
    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the given permission. This is used in the admin panel.
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Returns True if the user has permission to view the app in the admin.
        """
        return self.is_superuser
    def check_token(self, token):
        """Tokenni tekshiradi"""
        return self.token_user == token
    

class FollowInfo(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follow_info'
    )

    podpischik = ArrayField(models.UUIDField(), default=list, blank=True)  
    podpiski = ArrayField(models.UUIDField(), default=list, blank=True)  
    pending_requests = ArrayField(models.UUIDField(), default=list, blank=True)  
    limit = models.IntegerField(default=3) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follow_info'

    def __str__(self):
        return f"FollowInfo of {self.user.phone_number}"