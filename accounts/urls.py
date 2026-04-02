from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/deactivate/', views.user_deactivate, name='user_deactivate'),
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/password/', views.change_password, name='change_password'),
    path('register/', views.register, name='register'),
]
