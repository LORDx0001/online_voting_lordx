from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from . import views

schema_view = get_schema_view(
   openapi.Info(
      title="Online Voting API",
      default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=[],
)

urlpatterns = [
    path('', views.home, name='home'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('register/', views.register, name='register'),
    path('otp/verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('polls/', views.poll_list, name='poll_list'),
    path('vote/', views.vote, name='vote'),
    path('user/my-votes/', views.my_votes, name='my_votes'),
    path('staff/create-poll/', views.create_poll, name='create_poll'),
    path('staff/create-candidate/', views.create_candidate, name='create_candidate'),
    path('polls/<int:poll_id>/', views.poll_detail, name='poll_detail'),
    path('otp/resend-otp/', views.resend_otp, name='reset_otp'),
    path('user/reset-password/', views.reset_password, name='reset_password'),
    path('user/forgot-password/', views.forgot_password, name='forgot_password'),
    path('user/forgotpasswordconfirm/', views.forgot_password_confirm, name='forgot_password_confirm'),
    path('user/info/', views.user_info, name='user_info'),
    path('user/update-profile/', views.update_user_info, name='update_profile'),
    path('user/delete-account/', views.delete_user, name='delete_account'),
]
