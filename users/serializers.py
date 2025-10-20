# users/serializers.py

from rest_framework import serializers
from .models import CustomUser,UserImage,Purpose,Interest,UserProfile,UserProfileExtension,Region,District


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']


class DistrictSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name', 'region']

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
        fields = ['name']

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
            'user', 'birth_year', 'gender', 'weight','height','region', 'district', 'latitude', 'longitude',
            'purposes', 'interests', 'images','bio', 'instagram_link', 'telegram_link','tiktok_link'
        ]
class UserProfileSerializer(serializers.ModelSerializer):
    purposes = PurposeSerializer(many=True, read_only=True)
    interests = InterestSerializer(many=True, read_only=True)
    images = UserImageSerializer(many=True, read_only=True)

    # 🔹 Bitta matn sifatida chiqadi
    manzil = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'birth_year',
            'gender',
            'manzil',
            'latitude',
            'longitude',
            'weight',
            'height',
            'purposes',
            'interests',
            'images',
            'bio',
            'instagram_link',
            'telegram_link',
            'tiktok_link'
        ]

    def get_manzil(self, obj):
        # 🔹 Region va district nomlarini bitta string qilib birlashtiramiz
        if obj.region and obj.district:
            return f"{obj.region.name}, {obj.district.name}"
        else:
            return "O‘zbekiston"
    
class CustomUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['uuid', 'name', 'phone', 'email', 'token', 'profile']