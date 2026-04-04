from django.contrib import admin
from .models import Prediction

class PredictionAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'risk_score_percent', 'risk_category', 'model_used', 'prediction_date', 'triggered_by')
    list_filter = ('risk_category', 'model_used', 'triggered_by')
    search_fields = ('patient_id__name', 'patient_id__patient_id')
    readonly_fields = ('prediction_date', 'risk_score', 'risk_category', 'model_used', 'shap_values', 'triggered_by')
    
    def patient_name(self, obj):
        return obj.patient_id.name
    patient_name.short_description = 'Patient'

    def risk_score_percent(self, obj):
        return f"{round(obj.risk_score * 100, 1)}%"
    risk_score_percent.short_description = 'Score'

admin.site.register(Prediction, PredictionAdmin)
