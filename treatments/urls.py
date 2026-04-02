from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:patient_id>/update/', views.update_treatment, name='update_treatment'),
    path('<uuid:patient_id>/visit/', views.add_monitoring_visit, name='add_monitoring_visit'),
    path('visit/<int:visit_id>/edit/', views.monitoring_visit_update, name='monitoring_visit_update'),
    path('visit/<int:visit_id>/delete/', views.monitoring_visit_delete, name='monitoring_visit_delete'),
]
