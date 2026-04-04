from django.contrib import admin
from .models import Treatment, MonitoringVisit

class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'Bacilloscopy_Sputum', 'Sputum_Culture', 'Outcome_Status')
    list_filter = ('Outcome_Status', 'Supervised_Treatment')
    search_fields = ('patient__name', 'patient__patient_id')
    
    def patient_name(self, obj):
        return obj.patient.name
    patient_name.short_description = 'Patient'

class MonitoringVisitAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'visit_month', 'visit_date', 'bacilloscopy_result', 'weight', 'bmi', 'recorded_by')
    list_filter = ('visit_month', 'bacilloscopy_result', 'recorded_by')
    search_fields = ('patient__name', 'patient__patient_id')
    
    def patient_name(self, obj):
        return obj.patient.name
    patient_name.short_description = 'Patient'

admin.site.register(Treatment, TreatmentAdmin)
admin.site.register(MonitoringVisit, MonitoringVisitAdmin)
