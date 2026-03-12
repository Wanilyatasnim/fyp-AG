from django import forms
from .models import Treatment, MonitoringVisit

class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        fields = [
            'Supervised_Treatment', 'Days_In_Treatment', 'Outcome_Status',
            'Bacilloscopy_Sputum', 'Bacilloscopy_Sputum_2', 'Bacilloscopy_Other', 'Sputum_Culture',
            'Rifampicin', 'Isoniazid', 'Ethambutol', 'Streptomycin', 
            'Pyrazinamide', 'Ethionamide', 'Other_Drugs'
        ]

class MonitoringVisitForm(forms.ModelForm):
    class Meta:
        model = MonitoringVisit
        fields = ['visit_month', 'bacilloscopy_result', 'visit_date', 'clinical_notes']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'clinical_notes': forms.Textarea(attrs={'rows': 3}),
        }
