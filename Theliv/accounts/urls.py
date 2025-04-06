from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('logout/', views.user_logout, name='logout'),
    path('totp/', views.totp_setup, name='totp_setup'),
]