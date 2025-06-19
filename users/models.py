import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not phone:
            raise ValueError("Phone is required")

        email = self.normalize_email(email)
        token = secrets.token_hex(16)
        user = self.model(email=email, phone=phone, token=token, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, phone, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True, db_index=True)
    sms_code = models.CharField(max_length=6, blank=True, null=True)
    sms_code_expires = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(16)
        super().save(*args, **kwargs)
        
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['token']),
            models.Index(fields=['uuid']),
        ]
        ordering = ['-created_at']


class Purpose(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

def interest_image_upload_path(instance, filename):
    return f"interest_images/{instance.id}/{filename}"

class Interest(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to=interest_image_upload_path, blank=True, null=True)

    def __str__(self):
        return self.title




class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Erkak'),
        ('female', 'Ayol'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    birth_year = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

    region = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True,null=True)
    height  = models.FloatField(blank=True,null=True)

    purposes = models.ManyToManyField(Purpose, blank=True)
    interests = models.ManyToManyField(Interest, blank=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
    

    
def user_image_upload_path(instance, filename):
    return f"user_images/{instance.user_profile.user.id}/{filename}"

class UserImage(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=user_image_upload_path)
    is_main = models.BooleanField(default=False)
    is_auth = models.BooleanField(default=False)
    def __str__(self):
        return f"Image for {self.user_profile.user.email} (Main: {self.is_main})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_profile'],
                condition=models.Q(is_main=True),
                name='unique_main_image_per_user'
            )
        ]

class UserProfileExtension(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='extension')

    daily_requests_limit = models.PositiveIntegerField(default=50)
    requests_left = models.PositiveIntegerField(default=50)
    last_reset = models.DateTimeField(auto_now_add=True)

    subscribers = models.ManyToManyField(UserProfile, related_name='subscribed_to', blank=True)
    requests = models.ManyToManyField(UserProfile, related_name='requested_profiles', blank=True)
    blocked_users = models.ManyToManyField(UserProfile, related_name='blocked_by', blank=True)

    def __str__(self):
        return f"Extension of {self.user_profile.user.email}"

    def reset_requests_if_needed(self):
        if timezone.now() - self.last_reset >= timedelta(days=1):
            self.requests_left = self.daily_requests_limit
            self.last_reset = timezone.now()
            self.save()