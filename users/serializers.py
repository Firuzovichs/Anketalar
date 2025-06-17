# users/serializers.py

from rest_framework import serializers
from .models import CustomUser,UserImage,Purpose,Interest,UserProfile,UserProfileExtension

class RequestSMSCodeSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()
    phone = serializers.CharField()

class VerifySMSCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
class PurposeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purpose
        fields = ['id', 'title']

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'title', 'image']

class UserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserImage
        fields = ['id', 'image', 'is_main', 'is_auth']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'phone']

class UserProfileExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileExtension
        fields = ['daily_requests_limit', 'requests_left', 'last_reset']

class FullUserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    purposes = PurposeSerializer(many=True)
    interests = InterestSerializer(many=True)
    images = UserImageSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'birth_year', 'gender', 'region', 'district', 'latitude', 'longitude',
            'purposes', 'interests', 'images'
        ]

    