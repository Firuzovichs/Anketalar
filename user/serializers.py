from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['nickname', 'phone_number', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Parolni saqlashdan oldin shifrlaymiz
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'password']

class AuthCustomUserSerializer(serializers.Serializer):
    username = serializers.CharField()  # email yoki phone_number uchun umumiy maydon
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # Foydalanuvchini email yoki phone_number bo'yicha qidirmoq
        user = None
        if '@' in username:  # Email tekshiruvi
            user = get_user_model().objects.filter(email=username).first()
        else:  # Telefon raqami bo'yicha qidirish
            user = get_user_model().objects.filter(phone_number=username).first()

        if user is None:
            raise AuthenticationFailed('Invalid credentials')

        if not user.check_password(password):
            raise AuthenticationFailed('Invalid credentials')

        attrs['user'] = user
        return attrs