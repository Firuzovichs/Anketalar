
from django.urls import path
from .views import UserImageAPIView,UpdateUserProfileAPIView,GetUserByTokenAPIView,NearbyProfilesAPIView,SomeProtectedAPIView,FilteredUserProfileAPIView,SendRequestAPIView,UploadUserImagesAPIView,ProfileUpdateAPIView,RequestSMSCodeView, VerifySMSCodeView,LoginView,ForgotPasswordRequestAPIView,VerifyCodeAPIView,ResetPasswordAPIView


urlpatterns = [

    path('profile-datas/', GetUserByTokenAPIView.as_view(), name='get_data_profile'),
    path('profile-image-update/', UserImageAPIView.as_view(), name='update_image_profile'),
    path('profile-data-update/', UpdateUserProfileAPIView.as_view(), name='update_data_profile'),
    path('auth/request-code/', RequestSMSCodeView.as_view(), name='request_sms_code'),
    path('auth/verify-code/', VerifySMSCodeView.as_view(), name='verify_sms_code'),
    path('auth/login/', LoginView.as_view(), name='jwt-login'),
    path('auth/forgot-password/', ForgotPasswordRequestAPIView.as_view(), name='forgot_password'),
    path('auth/verify-code-forgotp/', VerifyCodeAPIView.as_view(), name='verify_code_forgot'),
    path('auth/reset-password/', ResetPasswordAPIView.as_view(), name='reset_password'),
    path('auth/profile/update-datas/', ProfileUpdateAPIView.as_view(), name='profile_update'),
    path('auth/profile/upload-images/', UploadUserImagesAPIView.as_view(), name='update_images'),
    path('auth/profile/send-request/', SendRequestAPIView.as_view(), name='send_request'),
    path('search/profile', FilteredUserProfileAPIView.as_view(), name='search_profile'),
    path('check/limit/', SomeProtectedAPIView.as_view(), name='limittekshirish'),
    path('search/bylatlong/', NearbyProfilesAPIView.as_view(), name='latlongbilanqidirish'),
]
