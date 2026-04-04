from django.urls import path
from . import views

urlpatterns = [
    path('', views.population_dashboard, name='population_dashboard'),
    path('clinician/', views.clinician_dashboard, name='clinician_dashboard'),
    path('analytics/', views.analyst_dashboard, name='analyst_dashboard'),
    path('model-performance/', views.model_performance, name='model_performance'),
    path('export/', views.export_anonymized_data, name='export_anonymized_data'),
    path('patient/<uuid:patient_id>/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/<uuid:patient_id>/predict/', views.generate_prediction, name='generate_prediction'),
]
