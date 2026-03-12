from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/deactivate/', views.user_deactivate, name='user_deactivate'),
]
