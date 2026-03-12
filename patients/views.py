from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Patient
from .forms import PatientForm

def is_clinician_or_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'CLINICIAN']

@login_required
@user_passes_test(is_clinician_or_admin)
def patient_list(request):
    patients = Patient.objects.all().order_by('-created_at')
    
    # Implement basic search filter
    query = request.GET.get('q')
    if query:
        patients = patients.filter(name__icontains=query)
        
    return render(request, 'patients/patient_list.html', {'patients': patients})

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
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    from django.shortcuts import redirect
    return redirect('patient_dashboard', patient_id=patient_id)
