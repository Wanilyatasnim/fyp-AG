from django.urls import path
from . import views

urlpatterns = [
    path('', views.population_dashboard, name='population_dashboard'),
    path('patient/<uuid:patient_id>/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/<uuid:patient_id>/predict/', views.generate_prediction, name='generate_prediction'),
]
