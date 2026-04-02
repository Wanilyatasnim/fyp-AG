from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Patient
from .forms import PatientForm

from django.core.paginator import Paginator

def is_clinician_or_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'CLINICIAN']

@login_required
def patient_list(request):
    patient_query = Patient.objects.all().order_by('-created_at')
    
    # Implement basic search filter
    query = request.GET.get('q')
    if query:
        patient_query = patient_query.filter(name__icontains=query)
        
    paginator = Paginator(patient_query, 20) # Show 20 patients per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'patients/patient_list.html', {'page_obj': page_obj, 'query': query})

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.save()
            messages.success(request, f'Patient {patient.name} created successfully with ID {patient.patient_id}.')
            return redirect('patient_list')
    else:
        form = PatientForm()
    
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Add Patient'})

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_update(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Patient {patient.name} updated successfully.')
            return redirect('patient_detail', patient_id=patient.patient_id)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Edit Patient'})

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_delete(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    if request.method == 'POST':
        name = patient.name
        patient.delete()
        messages.success(request, f'Patient {name} has been deleted.')
        return redirect('patient_list')
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    return redirect('patient_dashboard', patient_id=patient_id)
