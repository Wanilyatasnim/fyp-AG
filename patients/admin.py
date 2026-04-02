from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'name', 'Age', 'created_at', 'created_by')
    search_fields = ('name', 'patient_id')
    list_filter = ('created_at', 'Sex')
