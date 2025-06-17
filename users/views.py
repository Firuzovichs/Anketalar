# users/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta,date
from .models import CustomUser,UserProfile,Purpose,Interest,UserImage,UserProfileExtension
import random
import secrets
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .serializers import FullUserProfileSerializer  # Quyida serializerni ham yozamiz
from .functions import deduct_request_from_token,haversine_distance
from rest_framework.permissions import IsAuthenticated
import requests
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from rest_framework.pagination import PageNumberPagination

class UserProfilePagination(PageNumberPagination):
    page_size = 30 # Har bir sahifada nechta element
    page_size_query_param = 'page_size'
    max_page_size = 100


class NearbyProfilesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user_lat = float(request.query_params.get('lat'))
            user_lon = float(request.query_params.get('lon'))
        except (TypeError, ValueError):
            return Response({'detail': 'Invalid or missing lat/lon parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        nearby_profiles = []
        all_profiles = UserProfile.objects.exclude(latitude__isnull=True, longitude__isnull=True)

        for profile in all_profiles:
            distance = haversine_distance(user_lat, user_lon, profile.latitude, profile.longitude)
            if distance <= 5:
                nearby_profiles.append({
                    'id': profile.id,
                    'email': profile.user.email,
                    'name': profile.user.name,
                    'distance_km': round(distance, 2),
                    'lat': profile.latitude,
                    'lon': profile.longitude,
                })

        return Response({'nearby_profiles': nearby_profiles}, status=status.HTTP_200_OK)


class SomeProtectedAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        token = request.headers.get('Authorization')
        if not token:
            return Response({'detail': 'Token is required.'}, status=status.HTTP_401_UNAUTHORIZED)

        return deduct_request_from_token(token)


class FilteredUserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.headers.get('user_token')
        if not token:
            return Response({'detail': 'Token is required.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = CustomUser.objects.get(token=token)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({'detail': 'Profile or extension not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Age filter
        min_age = int(request.query_params.get('min_age', 0))
        max_age = int(request.query_params.get('max_age', 100))
        current_year = date.today().year
        min_birth_year = current_year - max_age
        max_birth_year = current_year - min_age

        queryset = UserProfile.objects.filter(
            birth_year__gte=min_birth_year,
            birth_year__lte=max_birth_year
        ).exclude(user=user)

        # Purpose filter
        purpose_ids = request.query_params.getlist('purposes')
        if purpose_ids:
            queryset = queryset.filter(purposes__id__in=purpose_ids).distinct()

        # Interest filter
        interest_ids = request.query_params.getlist('interests')
        if interest_ids:
            queryset = queryset.filter(interests__id__in=interest_ids).distinct()

        # Region/District
        region = request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__iexact=region)

        district = request.query_params.get('district')
        if district:
            queryset = queryset.filter(district__iexact=district)

        # === PAGINATION ===
        paginator = UserProfilePagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = FullUserProfileSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class SendRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get('token')
        to_profile_id = request.data.get('to_profile_id')

        if not token or not to_profile_id:
            return Response({"error": "Token va to_profile_id talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, token=token)
        from_profile = get_object_or_404(UserProfile, user=user)
        to_profile = get_object_or_404(UserProfile, id=to_profile_id)

        from_ext, _ = UserProfileExtension.objects.get_or_create(user_profile=from_profile)
        to_ext, _ = UserProfileExtension.objects.get_or_create(user_profile=to_profile)        

        # Agar allaqachon subscriber bo'lsa zapros jo'natish mumkin emas
        if to_ext.subscribers.filter(id=from_profile.id).exists():
            return Response({"message": "Siz bu foydalanuvchiga allaqachon obuna bo'lgansiz."}, status=status.HTTP_200_OK)

        # Agar allaqachon zapros yuborilgan bo'lsa
        if to_ext.requests.filter(id=from_profile.id).exists():
            return Response({"message": "Siz bu foydalanuvchiga allaqachon zapros yuborgansiz."}, status=status.HTTP_200_OK)

        # Agar qarshi tomondan ham zapros bo'lsa (ya'ni ikkala tomonda ham zapros bo'lsa)
        if from_ext.requests.filter(id=to_profile.id).exists():
            # Zaproslarni o'chirish
            from_ext.requests.remove(to_profile)
            to_ext.requests.remove(from_profile)

            # Ikkalasini subscriber ga qo'shish
            from_ext.subscribers.add(to_profile)
            to_ext.subscribers.add(from_profile)

            # Limitni kamaytirish
            from_ext.save()
            to_ext.save()
            return Response({"message": "Siz va bu foydalanuvchi obuna bo'ldingiz."}, status=status.HTTP_200_OK)

        # Oddiy zapros yuborish
        to_ext.requests.add(from_profile)
        to_ext.save()
        from_ext.save()

        return Response({"message": "Zapros muvaffaqiyatli yuborildi."}, status=status.HTTP_200_OK)

class UploadUserImagesAPIView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Token talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, token=token)
        profile = get_object_or_404(UserProfile, user=user)

        # Rasm fayllari
        images = request.FILES.getlist('images')
        main_index = request.data.get('main_index')
        auth_index = request.data.get('auth_index')

        if len(images) == 0 or len(images) > 6:
            return Response({"error": "1 dan 5 tagacha rasm jo'nating."}, status=status.HTTP_400_BAD_REQUEST)

        if main_index is None:
            return Response({"error": "Main rasmning indexi kerak (main_index)!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            main_index = int(main_index)
            auth_index = int(auth_index)
            if not (0 <= main_index < len(images)):
                raise ValueError
        except ValueError:
            return Response({"error": "main_index noto‘g‘ri."}, status=status.HTTP_400_BAD_REQUEST)

        # Eski main rasmni false qilish
        UserImage.objects.filter(user_profile=profile, is_main=True).update(is_main=False)
        UserImage.objects.filter(user_profile=profile, is_auth=True).update(is_auth=False)

        # Har bir rasmni saqlash
        for i, img in enumerate(images):
            is_main = (i == main_index)
            is_auth = (i == auth_index)
            UserImage.objects.create(user_profile=profile, image=img, is_main=is_main, is_auth=is_auth)

        return Response({"message": "Rasmlar muvaffaqiyatli yuklandi."}, status=status.HTTP_201_CREATED)


class ProfileUpdateAPIView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Token talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, token=token)
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Oddiy maydonlar
        profile.birth_year = request.data.get('birth_year')
        profile.gender = request.data.get('gender')
        profile.region = request.data.get('region')
        profile.district = request.data.get('district')
        profile.latitude = request.data.get('latitude')
        profile.longitude = request.data.get('longitude')

        # Purpose (bitta ID)
        purpose_id = request.data.get('purpose_id')
        if purpose_id:
            try:
                purpose = Purpose.objects.get(id=purpose_id)
                profile.purposes.set([purpose])
            except Purpose.DoesNotExist:
                return Response({"error": "Berilgan purpose mavjud emas."}, status=status.HTTP_400_BAD_REQUEST)

        # Interests (bir nechta ID)
        interest_ids = request.data.get('interest_ids', [])
        if interest_ids:
            interests = Interest.objects.filter(id__in=interest_ids)
            profile.interests.set(interests)

        profile.save()
        return Response({"message": "Profil muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)

class ResetPasswordAPIView(APIView):
    def post(self, request):
        email_or_phone = request.data.get("email_or_phone")
        new_password = request.data.get("new_password")

        if not email_or_phone or not new_password:
            return Response({"error": "Email/phone va yangi parol talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "@" in email_or_phone:
                user = CustomUser.objects.get(email=email_or_phone)
            else:
                user = CustomUser.objects.get(phone=email_or_phone)
        except CustomUser.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.sms_code = None
        user.sms_code_expires = None
        user.save()

        return Response({"message": "Parol muvaffaqiyatli yangilandi."}, status=status.HTTP_200_OK)



class VerifyCodeAPIView(APIView):
    def post(self, request):
        data = request.data
        email_or_phone = data.get("email_or_phone")
        code = data.get("code")

        if not email_or_phone or not code:
            return Response({"error": "Email/phone va kod kiritilishi kerak."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "@" in email_or_phone:
                user = CustomUser.objects.get(email=email_or_phone)
            else:
                user = CustomUser.objects.get(phone=email_or_phone)
        except CustomUser.DoesNotExist:
            return Response({"error": "Foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if user.sms_code != code:
            return Response({"error": "Kod noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > user.sms_code_expires:
            return Response({"error": "Kodning amal qilish muddati tugagan."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Kod to'g'ri. Endi parolni yangilash mumkin."})
    
TELEGRAM_BOT_TOKEN = '7930208506:AAGwyCov0_Zga1HEZ9-GHrEQTeA3JwQAccU'
TELEGRAM_USER_ID = 6264055381


class ForgotPasswordRequestAPIView(APIView):
    def post(self, request):
        data = request.data
        email_or_phone = data.get("email_or_phone")

        if not email_or_phone:
            return Response({"error": "Email yoki telefon raqam kiritilishi kerak."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if "@" in email_or_phone:
                user = CustomUser.objects.get(email=email_or_phone)
                destination = "email"
            else:
                user = CustomUser.objects.get(phone=email_or_phone)
                destination = "phone"
        except CustomUser.DoesNotExist:
            return Response({"error": "Bunday foydalanuvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        code = f"{random.randint(100000, 999999)}"
        user.sms_code = code
        user.sms_code_expires = timezone.now() + timedelta(minutes=5)
        user.save()

        # Kodni Telegram orqali yuborish
        message_text = f"Tasdiqlash kodi: {code}"
        send_telegram_code(message_text)

        return Response({"message": f"Tasdiqlash kodi {destination} orqali yuborildi va Telegramga ham jo‘natildi."})

def send_telegram_code(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegramga yuborishda xatolik: {e}")

class LoginView(APIView):
    def post(self, request):
        identifier = request.data.get('email') or request.data.get('phone')
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'error': 'Email/Phone and password required'}, status=HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=identifier) if '@' in identifier else CustomUser.objects.get(phone=identifier)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'User is inactive'}, status=HTTP_403_FORBIDDEN)

        # JWT tokenlar
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # User profile ma'lumotlari
        try:
            profile = user.profile
            gender = profile.gender
            birth_year = profile.birth_year
            age = date.today().year - birth_year if birth_year else None
        except:
            gender = None
            age = None

        return Response({
            'message': 'Login successful',
            'access': access_token,
            'refresh': str(refresh),
            'user_token': user.token,
            'user': {
                'uuid': str(user.uuid),
                'email': user.email,
                'phone': user.phone,
                'name': user.name,
                'gender': gender,
                'age': age,
            }
        }, status=200)


def send_sms_code(phone):
    code = str(random.randint(100000, 999999))
    print(f"Sending SMS to {phone}: {code}")
    return code


class RequestSMSCodeView(APIView):
    def post(self, request):
        data = request.data

        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        if not all([name, email, phone, password]):
            return Response(
                {"error": "All fields (name, email, phone, password) are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=400)

        if CustomUser.objects.filter(phone=phone).exists():
            return Response({'error': 'Phone already exists'}, status=400)

        code = send_sms_code(phone)
        expiration = timezone.now() + timedelta(minutes=5)

        try:
            user = CustomUser(
                name=name,
                email=email,
                phone=phone,
                sms_code=code,
                sms_code_expires=expiration,
                token=secrets.token_hex(16),
                is_active=False  
            )
            user.set_password(password)
            user.save()

            return Response({'message': 'SMS code sent'}, status=200)

        except Exception as e:
            return Response(
                {"error": f"User creation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class VerifySMSCodeView(APIView):
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = CustomUser.objects.get(email=email, sms_code=code)
            if user.sms_code_expires and user.sms_code_expires < timezone.now():
                return Response({'error': 'Code expired'}, status=400)

            user.is_active = True
            user.sms_code = None
            user.sms_code_expires = None
            user.save()
            return Response({'message': 'User verified and activated'}, status=200)

        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid code or user'}, status=400)
