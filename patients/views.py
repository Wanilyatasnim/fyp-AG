from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Patient
from .forms import PatientForm

def is_clinician_or_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'CLINICIAN']

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_list(request):
    """
    List of patients with advanced search and role-based filtering.
    Restricted to Clinicians and Admins. Analysts use the Analytics Hub.
    """
    # 1. Scoping: Clinicians only see their own. Admins see all.
    if request.user.role == 'CLINICIAN':
        patient_query = Patient.objects.filter(assigned_clinician=request.user)
    else:
        patient_query = Patient.objects.all()

    patient_query = patient_query.order_by('-created_at')
    
    # 2. Search & Filters
    q = request.GET.get('q')
    if q:
        patient_query = patient_query.filter(Q(name__icontains=q) | Q(patient_id__icontains=q))
        
    status = request.GET.get('status')
    if status:
        patient_query = patient_query.filter(treatment_status=status)
        
    risk = request.GET.get('risk')
    if risk:
        patient_query = patient_query.filter(predictions__risk_category=risk).distinct()
        
    paginator = Paginator(patient_query, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
        
    return render(request, 'patients/patient_list.html', {
        'page_obj': page_obj, 'query': q, 'status': status, 'risk': risk
    })

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            if request.user.role == 'CLINICIAN':
                patient.assigned_clinician = request.user
            patient.save()
            messages.success(request, f'Patient {patient.name} created.')
            return redirect('patient_list')
    else:
        form = PatientForm()
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Add Patient'})

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_update(request, patient_id):
    """
    Hard-Link scoping for updates: Clinicians can only query their own.
    """
    if request.user.role == 'CLINICIAN':
        patient = get_object_or_404(Patient, patient_id=patient_id, assigned_clinician=request.user)
    else:
        patient = get_object_or_404(Patient, patient_id=patient_id)

    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Patient {patient.name} updated.')
            return redirect('patient_dashboard', patient_id=patient.patient_id)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Edit Patient'})

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_delete(request, patient_id):
    """
    Hard-Link scoping for deletions: Clinicians can only query their own.
    """
    if request.user.role == 'CLINICIAN':
        patient = get_object_or_404(Patient, patient_id=patient_id, assigned_clinician=request.user)
    else:
        patient = get_object_or_404(Patient, patient_id=patient_id)

    if request.method == 'POST':
        name = patient.name
        patient.delete()
        messages.success(request, f'Patient {name} deleted.')
        return redirect('patient_list')
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})

@login_required
def patient_detail(request, patient_id):
    """Unified redirect to dashboard (scoping is handled there)."""
    return redirect('patient_dashboard', patient_id=patient_id)
