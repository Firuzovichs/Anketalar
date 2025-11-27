from django.urls import path
from .views import VerifyStartAPIView,VerifyCheckAPIView,RegisterAPIView
urlpatterns = [
    path('verifyStart/', VerifyStartAPIView.as_view(), name='verify'),
    path('verifyCheck/', VerifyCheckAPIView.as_view(), name="verify-check"),
    path('register/', RegisterAPIView.as_view(), name="register"),
]