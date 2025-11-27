# project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/v3/admin/', admin.site.urls),
    path('api/v3/', include('users.urls')),  # api prefix
    path('api/v3/mobile/', include('mobile.urls')),  # api prefix
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
