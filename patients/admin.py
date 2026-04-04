from django.contrib import admin
from .models import Patient

class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'patient_id_short', 'Age', 'Sex', 'treatment_status', 'assigned_clinician', 'created_at')
    list_filter = ('treatment_status', 'Sex', 'Race', 'assigned_clinician')
    search_fields = ('name', 'patient_id')
    readonly_fields = ('patient_id', 'created_at')
    
    def patient_id_short(self, obj):
        return str(obj.patient_id)[:8] + '...'
    patient_id_short.short_description = 'ID'

admin.site.register(Patient, PatientAdmin)
