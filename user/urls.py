from django.urls import path
from .views import CustomTokenObtainPairView,CreateUserView,AddRequestView,PendingRequestsView,AcceptFollowRequestView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('create/user/', CreateUserView.as_view(), name='create_user'),
    path('follow/add/', AddRequestView.as_view(), name='add-follower'),
    path('user/requests/', PendingRequestsView.as_view(), name='user-requests'),
    path('user/acceptrequests/', AcceptFollowRequestView.as_view(), name='accept-requests'),                
]