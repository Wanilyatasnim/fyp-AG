from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:patient_id>/update/', views.update_treatment, name='update_treatment'),
    path('<uuid:patient_id>/visit/', views.add_monitoring_visit, name='add_monitoring_visit'),
]
