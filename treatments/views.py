from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Treatment, MonitoringVisit
from .forms import TreatmentForm, MonitoringVisitForm
from patients.models import Patient

@login_required
def update_treatment(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    treatment, created = Treatment.objects.get_or_create(patient=patient)
    
    if request.method == 'POST':
        form = TreatmentForm(request.POST, instance=treatment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Treatment registered/updated successfully.')
            return redirect('patient_detail', patient_id=patient.patient_id)
    else:
        form = TreatmentForm(instance=treatment)
        
    return render(request, 'treatments/treatment_form.html', {
        'form': form,
        'patient': patient
    })

@login_required
def add_monitoring_visit(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    treatment, created = Treatment.objects.get_or_create(patient=patient)
    
    if request.method == 'POST':
        form = MonitoringVisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.treatment = treatment
            visit.recorded_by = request.user
            try:
                visit.save()
                messages.success(request, 'Monitoring visit recorded successfully.')
                return redirect('patient_detail', patient_id=patient.patient_id)
            except Exception as e:
                messages.error(request, f'Failed to record visit: {e}')
    else:
        form = MonitoringVisitForm()
        
    visits = MonitoringVisit.objects.filter(patient=patient).order_by('visit_month')
    
    return render(request, 'treatments/visit_form.html', {
        'form': form,
        'patient': patient,
        'visits': visits
    })
