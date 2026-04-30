from django import forms
from .models import Patient
from treatments.models import Treatment

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        exclude = ('patient_id', 'created_at', 'created_by', 'assigned_clinician')
        widgets = {
            'Notification_Date': forms.DateInput(attrs={'type': 'date'}),
            'treatment_start_date': forms.DateInput(attrs={'type': 'date'}),
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'

class TreatmentForm(forms.ModelForm):
    Days_In_Treatment = forms.IntegerField(
        required=True,
        min_value=0,
        help_text="Number of days since treatment started (0 if just started)"
    )

    class Meta:
        model = Treatment
        exclude = ('patient',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
