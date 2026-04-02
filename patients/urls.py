from django.urls import path
from . import views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('new/', views.patient_create, name='patient_create'),
    path('<uuid:patient_id>/', views.patient_detail, name='patient_detail'),
    path('<uuid:patient_id>/edit/', views.patient_update, name='patient_update'),
    path('<uuid:patient_id>/delete/', views.patient_delete, name='patient_delete'),
]
