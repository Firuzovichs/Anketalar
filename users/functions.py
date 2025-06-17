from .models import CustomUser
from rest_framework.response import Response
from rest_framework import status
from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1, lon1, lat2, lon2):
    # Yer radiusi kilometrda
    R = 6371.0

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def deduct_request_from_token(token):
    try:
        # Foydalanuvchini token orqali topamiz
        user = CustomUser.objects.get(token=token)
        profile = user.profile
        extension = profile.extension

        # Har kuni yangilash kerak bo‘lsa, uni ham tekshirib yangilaymiz
        extension.reset_requests_if_needed()

        if extension.requests_left <= 0:
            return Response({'detail': 'Request limit reached.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # requests_left ni kamaytirish
        extension.requests_left -= 1
        extension.save()

        return Response({'detail': 'Request counted successfully.', 'requests_left': extension.requests_left}, status=status.HTTP_200_OK)

    except CustomUser.DoesNotExist:
        return Response({'detail': 'Invalid token.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'detail': f'Error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)