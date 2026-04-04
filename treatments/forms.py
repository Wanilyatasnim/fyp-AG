from django import forms
from .models import MonitoringVisit, Treatment

class TreatmentForm(forms.ModelForm):
    class Meta:
        model = Treatment
        exclude = ('patient',)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'

class MonitoringVisitForm(forms.ModelForm):
    # Specific symptoms as boolean fields for a better UI in the form
    symptom_cough = forms.BooleanField(required=False, label="Persistent Cough")
    symptom_dyspnea = forms.BooleanField(required=False, label="Dyspnea (Shortness of Breath)")
    symptom_fever = forms.BooleanField(required=False, label="Fever")
    symptom_weight_loss = forms.BooleanField(required=False, label="Weight Loss")
    
    class Meta:
        model = MonitoringVisit
        fields = ['visit_month', 'visit_date', 'bacilloscopy_result', 'weight', 'bmi', 'adverse_events', 'clinical_notes']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'clinical_notes': forms.Textarea(attrs={'rows': 3}),
            'adverse_events': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        
        # Load symptoms from JSON if instance exists
        if self.instance and self.instance.symptoms:
            s = self.instance.symptoms
            self.fields['symptom_cough'].initial = s.get('cough', False)
            self.fields['symptom_dyspnea'].initial = s.get('dyspnea', False)
            self.fields['symptom_fever'].initial = s.get('fever', False)
            self.fields['symptom_weight_loss'].initial = s.get('weight_loss', False)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Pack boolean fields back into JSON
        instance.symptoms = {
            'cough': self.cleaned_data.get('symptom_cough'),
            'dyspnea': self.cleaned_data.get('symptom_dyspnea'),
            'fever': self.cleaned_data.get('symptom_fever'),
            'weight_loss': self.cleaned_data.get('symptom_weight_loss'),
        }
        if commit:
            instance.save()
        return instance
