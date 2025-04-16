from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AuthCustomUserSerializer,CustomUserCreateSerializer
from .models import FollowInfo
from django.contrib.auth import get_user_model
from uuid import UUID
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import requests

User = get_user_model()


class AcceptFollowRequestView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')  # Asosiy user (request qabul qilayotgan)
        token = request.data.get('token')
        pending_request_id = request.data.get('pending_request_id')  # So‘rov yuborgan user

        if not user_id or not token or not pending_request_id:
            return Response({'detail': 'user_id, token, and pending_request_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_uuid = UUID(user_id)
            requester_uuid = UUID(pending_request_id)
        except ValueError:
            return Response({'detail': 'Invalid UUID format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(uuid=user_uuid)
            requester = User.objects.get(uuid=requester_uuid)
        except User.DoesNotExist:
            return Response({'detail': 'User or pending requester not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_token(token):
            raise AuthenticationFailed('Invalid token.')

        # FollowInfo for both users
        try:
            follow_info = FollowInfo.objects.get(user=user)
        except FollowInfo.DoesNotExist:
            return Response({'detail': 'FollowInfo not found for user.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            requester_follow_info, _ = FollowInfo.objects.get_or_create(user=requester)
        except:
            return Response({'detail': 'FollowInfo not found or cannot be created for requester.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Agar pending_requestsda requester bor bo‘lsa
        if requester.uuid in follow_info.pending_requests:
            # Remove from pending
            follow_info.pending_requests.remove(requester.uuid)

            # Add to followers
            if requester.uuid not in follow_info.podpischik:
                follow_info.podpischik.append(requester.uuid)

            follow_info.save()

            # Add user to requester's podpiski
            if user.uuid not in requester_follow_info.podpiski:
                requester_follow_info.podpiski.append(user.uuid)
                requester_follow_info.save()

            return Response({
                'detail': 'Follow request accepted.',
                'user': str(user.uuid),
                'added_follower': str(requester.uuid),
                'user_podpischik': follow_info.podpischik,
                'requester_podpiski': requester_follow_info.podpiski
            }, status=status.HTTP_200_OK)

        else:
            return Response({'detail': 'This user is not in pending requests.'}, status=status.HTTP_400_BAD_REQUEST)


class PendingRequestsView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        token = request.data.get('token')

        if not user_id or not token:
            return Response({'detail': 'user_id and token are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return Response({'detail': 'Invalid UUID format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_token(token):
            raise AuthenticationFailed('Invalid token.')

        try:
            follow_info = FollowInfo.objects.get(user=user)
        except FollowInfo.DoesNotExist:
            return Response({'detail': 'FollowInfo not found for user.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'pending_requests': follow_info.pending_requests
        }, status=status.HTTP_200_OK)

class AddRequestView(APIView):
    def post(self, request):
        user_id = request.data.get('user')
        request_id = request.data.get('request_id')
        token = request.data.get('token')

        if not user_id or not request_id or not token:
            return Response({'detail': 'User, request_id and token are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_id == request_id:
            return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_uuid = UUID(user_id)
            requester_uuid = UUID(request_id)
        except ValueError:
            return Response({'detail': 'Invalid UUID format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(uuid=user_uuid)
            requester = User.objects.get(uuid=requester_uuid)
        except User.DoesNotExist:
            return Response({'detail': 'User or requester not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not requester.check_token(token):
            raise AuthenticationFailed('Invalid token for the requester.')

        # Requester uchun FollowInfo ob'ektini olish yoki yaratish
        requester_follow_info, created_requester = FollowInfo.objects.get_or_create(user=requester)

        # **Limitni avval tekshiramiz**
        if not created_requester and requester_follow_info.limit == 0:
            return Response({'detail': 'Request limit reached.'}, status=status.HTTP_403_FORBIDDEN)

        # User uchun FollowInfo ob'ektini olish yoki yaratish
        follow_info, _ = FollowInfo.objects.get_or_create(user=user)
        if requester.uuid in follow_info.podpischik:
            return Response({'detail': 'You are already a follower of this user.'}, status=status.HTTP_400_BAD_REQUEST)
        # Agar follow qilish uchun so‘rov yuborilmagan bo‘lsa
        if requester.uuid not in follow_info.pending_requests:
            follow_info.pending_requests.append(requester.uuid)
            follow_info.save()

            # Limitni kamaytirish (agar 0 dan katta bo‘lsa)
            if requester_follow_info.limit > 0:
                requester_follow_info.limit -= 1
                requester_follow_info.save()

        return Response({
            'detail': 'Follow request sent successfully.',
            'user': str(user.uuid),
            'pending_requests': follow_info.pending_requests,
            'requester_limit': requester_follow_info.limit
        }, status=status.HTTP_200_OK)
def verify_recaptcha(token):
    data = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': token
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = response.json()
    return result.get('success', False)
    
class CreateUserView(APIView):
    def post(self, request, *args, **kwargs):
        recaptcha_token = request.data.get('recaptcha_token')

        if not recaptcha_token:
            return Response({'detail': 'reCAPTCHA token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_recaptcha(recaptcha_token):
            return Response({'detail': 'Invalid reCAPTCHA token.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Userni yaratish
        serializer = CustomUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'uuid': str(user.uuid),
                'phone_number': user.phone_number,
                'email': user.email,
                'nickname': user.nickname
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        recaptcha_token = request.data.get('g-recaptcha-response')

        if not recaptcha_token or not verify_recaptcha(recaptcha_token):
            return Response({'detail': 'Invalid reCAPTCHA. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AuthCustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'is_superuser': user.is_superuser
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)