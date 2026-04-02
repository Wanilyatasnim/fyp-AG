from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Treatment, MonitoringVisit
from .forms import TreatmentForm, MonitoringVisitForm
from patients.models import Patient
from dashboard.views import is_clinician_or_admin

@login_required
@user_passes_test(is_clinician_or_admin)
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
@user_passes_test(is_clinician_or_admin)
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

@login_required
@user_passes_test(is_clinician_or_admin)
def monitoring_visit_update(request, visit_id):
    visit = get_object_or_404(MonitoringVisit, id=visit_id)
    if request.method == 'POST':
        form = MonitoringVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Monitoring visit updated successfully.')
            return redirect('add_monitoring_visit', patient_id=visit.patient.patient_id)
    else:
        form = MonitoringVisitForm(instance=visit)
        
    visits = MonitoringVisit.objects.filter(patient=visit.patient).order_by('visit_month')
    return render(request, 'treatments/visit_form.html', {
        'form': form,
        'patient': visit.patient,
        'visits': visits
    })

@login_required
@user_passes_test(is_clinician_or_admin)
def monitoring_visit_delete(request, visit_id):
    visit = get_object_or_404(MonitoringVisit, id=visit_id)
    patient_id = visit.patient.patient_id
    if request.method == 'POST':
        visit.delete()
        messages.success(request, 'Monitoring visit deleted.')
        return redirect('add_monitoring_visit', patient_id=patient_id)
    # Generic simple confirmation right in the view or using JS on frontend
    return render(request, 'patients/patient_confirm_delete.html', {
        'patient': visit.patient,
        'is_visit_delete': True,
        'visit': visit
    })
