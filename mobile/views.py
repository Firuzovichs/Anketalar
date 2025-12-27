from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta,date
import random
from django.core.mail import send_mail
from django.conf import settings
import requests
from users.models import CustomUser, PendingUser, UserProfile, Purpose, Interest, UserImage, Region, District
from django.db import transaction
from django.contrib.auth.hashers import make_password
from users.functions import send_email_code, send_telegram_code

class VerifyStartAPIView(APIView):
    def post(self, request):
        data = request.data
        email_or_phone = data.get("email_or_phone")

        if not email_or_phone:
            return Response({"error": "Email yoki telefon raqam kiritilishi kerak."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Random 6 xonali kod
        code = f"{random.randint(100000, 999999)}"
        expires = timezone.now() + timedelta(minutes=5)

        if "@" in email_or_phone:  # email
            pending, _ = PendingUser.objects.update_or_create(
                email=email_or_phone,
                defaults={"code": code, "code_expires": expires}
            )
            send_email_code(email_or_phone, code)
            destination = "email"

        else:  # telefon
            pending, _ = PendingUser.objects.update_or_create(
                phone=email_or_phone,
                defaults={"code": code, "code_expires": expires}
            )
            message = f"Tasdiqlash kodi: {code}"
            send_telegram_code(message, chat_ids=[settings.TELEGRAM_USER_ID1, settings.TELEGRAM_USER_ID2])
            destination = "telefon (Telegram bot)"

        return Response({"message": f"Tasdiqlash kodi {destination} orqali yuborildi."})
    


class VerifyCheckAPIView(APIView):
    def post(self, request):
        data = request.data
        email_or_phone = data.get("email_or_phone")
        code = data.get("code")

        if not email_or_phone or not code:
            return Response({"error": "Email/telefon va kod kerak."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            if "@" in email_or_phone:
                pending = PendingUser.objects.get(email=email_or_phone)
            else:
                pending = PendingUser.objects.get(phone=email_or_phone)
        except PendingUser.DoesNotExist:
            return Response({"error": "Tasdiqlash jarayoni topilmadi."},
                            status=status.HTTP_404_NOT_FOUND)

        # Kod muddati tugaganmi
        if pending.is_expired():
            return Response({"error": "Kod muddati tugagan."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Kod to‘g‘ri kiritilganmi
        if pending.code != code:
            return Response({"error": "Kod noto‘g‘ri."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Tasdiqlashni belgilash
        pending.is_verified = True
        pending.save()

        return Response({"message": "Foydalanuvchi muvaffaqiyatli tasdiqlandi.",
                         "temp_token": pending.id})  # keyingi register bosqichi uchun token
    
class RegisterAPIView(APIView):
    def post(self, request):
        data = request.data

        temp_token = data.get("temp_token")
        name = data.get("name")
        password = data.get("password")
        birth_year = data.get("birth_year")
        gender = data.get("gender")
        bio = data.get("bio")
        weight = data.get("weight")
        height = data.get("height")
        region_id = data.get("region_id")
        district_id = data.get("district_id")
        purposes_ids = data.get("purposes", "")
        interests_ids = data.get("interests", "")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        # Rasmlar
        main_image = request.FILES.get("images_main")
        auth_image = request.FILES.get("images_auth")
        other_images = request.FILES.getlist("images")  # 5 tagacha

        # Majburiy maydonlar
        if not all([temp_token, name, password, birth_year, gender]):
            return Response(
                {"error": "temp_token, name, password, birth_year va gender majburiy."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # PendingUser tekshirish
        try:
            pending_user = PendingUser.objects.get(id=temp_token, is_verified=True)
        except PendingUser.DoesNotExist:
            return Response({"error": "Tasdiqlangan foydalanuvchi topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        if len(other_images) > 5:
            return Response({"error": "5 tadan ortiq rasm yuklab bo‘lmaydi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # CustomUser yaratish
                email = pending_user.email if pending_user.email else None
                phone = pending_user.phone if pending_user.phone else None
                user = CustomUser.objects.create(
                    email=email,
                    phone=phone,
                    name=name,
                    password=make_password(password)
                )
                # Region va District
                region = Region.objects.filter(id=region_id).first() if region_id else None
                district = District.objects.filter(id=district_id).first() if district_id else None

                # UserProfile
                profile = UserProfile.objects.create(
                    user=user,
                    birth_year=birth_year,
                    gender=gender,
                    bio=bio,
                    weight=weight,
                    height=height,
                    region=region,
                    district=district,
                    latitude=latitude,
                    longitude=longitude
                )

                # Purposes
                if purposes_ids:
                    purposes_list = [int(i) for i in purposes_ids.split(",") if i.strip().isdigit()]
                    purposes = Purpose.objects.filter(id__in=purposes_list)
                    profile.purposes.set(purposes)

                # Interests
                if interests_ids:
                    interests_list = [int(i) for i in interests_ids.split(",") if i.strip().isdigit()]
                    interests = Interest.objects.filter(id__in=interests_list)
                    profile.interests.set(interests)

                # Rasmlar
                if main_image:
                    UserImage.objects.create(user_profile=profile, image=main_image, is_main=True)
                if auth_image:
                    UserImage.objects.create(user_profile=profile, image=auth_image, is_auth=True)
                for img in other_images:
                    UserImage.objects.create(user_profile=profile, image=img)

                # PendingUser o'chirish
                pending_user.delete()

                return Response(
                    {"message": "Foydalanuvchi muvaffaqiyatli ro‘yxatdan o‘tdi."},
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
