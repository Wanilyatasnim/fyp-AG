from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Q, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import StreamingHttpResponse
from datetime import timedelta
import json
import csv
import logging

from patients.models import Patient
from ml_engine.models import Prediction, ModelMetric
from patients.utils import get_clinical_recommendations

logger = logging.getLogger(__name__)

def is_clinician_or_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'CLINICIAN']

def is_analyst_or_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'ANALYST']

@login_required
def population_dashboard(request):
    # Redirect roles to their specialized dashboards
    if request.user.role == 'CLINICIAN':
        return redirect('clinician_dashboard')
    elif request.user.role == 'ANALYST':
        return redirect('analyst_dashboard')
        
    predictions = Prediction.objects.all()
    avg_risk    = predictions.aggregate(avg=Avg('risk_score'))['avg']
    high_risk   = predictions.filter(risk_category='High').values('patient_id').distinct().count()

    context = {
        'total_patients':   Patient.objects.count(),
        'avg_risk_score':   round(avg_risk, 2) if avg_risk else None,
        'high_risk_count':  high_risk,
        'patients':         Patient.objects.all().order_by('-created_at')[:20],
    }
    return render(request, 'dashboard/population_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'CLINICIAN' or u.is_staff)
def clinician_dashboard(request):
    """
    Clinician-specific dashboard showing assigned patients and alerts.
    """
    assigned_patients = Patient.objects.filter(assigned_clinician=request.user)
    active_count = assigned_patients.filter(treatment_status='Active').count()
    
    high_risk_patients = []
    for p in assigned_patients:
        latest = p.predictions.order_by('-prediction_date').first()
        if latest and latest.risk_category == 'High':
            high_risk_patients.append({
                'patient': p,
                'score': round(latest.risk_score * 100, 1)
            })
            
    today = timezone.now().date()
    window_start = today - timedelta(days=120)
    window_end = today - timedelta(days=75)
    
    needs_prediction = assigned_patients.filter(
        treatment_status='Active',
        treatment_start_date__gte=window_start,
        treatment_start_date__lte=window_end
    ).exclude(predictions__isnull=False)
    
    recent_activity = assigned_patients.order_by('-created_at')[:5]

    context = {
        'active_count': active_count,
        'high_risk_patients': high_risk_patients,
        'needs_prediction': needs_prediction,
        'recent_activity': recent_activity,
        'total_assigned': assigned_patients.count(),
    }
    return render(request, 'dashboard/clinician_dashboard.html', context)

@login_required
@user_passes_test(is_analyst_or_admin)
def analyst_dashboard(request):
    """
    Population-level analytics for analysts (No PII).
    """
    total_patients = Patient.objects.count()
    risk_dist = Prediction.objects.values('risk_category').annotate(count=Count('id'))
    sex_dist = Patient.objects.values('Sex').annotate(count=Count('id'))
    
    one_year_ago = timezone.now().date() - timedelta(days=365)
    trends = Patient.objects.filter(created_at__gte=one_year_ago)\
        .annotate(month=TruncMonth('created_at'))\
        .values('month')\
        .annotate(count=Count('id'))\
        .order_by('month')

    sex_labels = {1: 'Male', 2: 'Female'} 
    
    context = {
        'total_patients': total_patients,
        'risk_dist_json': json.dumps({item['risk_category']: item['count'] for item in risk_dist}),
        'sex_dist_json': json.dumps({sex_labels.get(item['Sex'], 'Other'): item['count'] for item in sex_dist}),
        'trend_labels': json.dumps([t['month'].strftime('%b %Y') for t in trends]),
        'trend_values': json.dumps([t['count'] for t in trends]),
    }
    return render(request, 'dashboard/analyst_dashboard.html', context)

@login_required
@user_passes_test(is_analyst_or_admin)
def model_performance(request):
    latest_metrics = ModelMetric.objects.order_by('-created_at').first()
    importance_json = json.dumps(latest_metrics.global_importance) if latest_metrics else '{}'

    context = {
        'metrics': latest_metrics,
        'importance_json': importance_json,
    }
    return render(request, 'dashboard/model_performance.html', context)

class Echo:
    def write(self, value): return value

@login_required
@user_passes_test(is_analyst_or_admin)
def export_anonymized_data(request):
    """
    Streams an anonymized CSV using .values() to ensure only specific, 
    non-identifiable columns are extracted from the database.
    """
    # Specifically select only the columns needed for research
    dataset = Patient.objects.values(
        'patient_id', 'Age', 'Sex', 'Race', 'Clinical_Form'
    )
    
    def rows():
        yield ['Anonymized_ID', 'Age', 'Sex', 'Race', 'TB_Type', 'Latest_Risk_Score', 'Latest_Risk_Category']
        for p in dataset:
            # Fetch latest prediction for this patient
            # Note: Since .values() returns a dict, we need a separate lookup or a joined query
            latest = Prediction.objects.filter(patient_id=p['patient_id']).order_by('-prediction_date').first()
            
            # Label mapping logic for Sex/Race/Form since .values() returns the raw integers
            sex_map = {1: 'Male', 2: 'Female'}
            
            yield [
                str(p['patient_id'])[:8], 
                p['Age'], 
                sex_map.get(p['Sex'], 'Other'),
                'Aggregated', # Race anonymized further if needed
                p['Clinical_Form'],
                latest.risk_score if latest else 'N/A',
                latest.risk_category if latest else 'N/A'
            ]
    
    writer = csv.writer(Echo())
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()), content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename="tb_ptld_anonymized_{timezone.now().date()}.csv"'
    return response

@login_required
def patient_dashboard(request, patient_id):
    """
    Detailed dashboard for a single patient. 
    Enforces 'Hard-Link' scoping: Clinicians can ONLY query their own patients.
    """
    # 1. First Wall: Role check
    if request.user.role == 'ANALYST':
        messages.error(request, "Access denied: Analysts cannot view individual records.")
        return redirect('analyst_dashboard')
        
    # 2. Second Wall: Hard-link Query Scoping
    if request.user.role == 'CLINICIAN':
        # Clinician can ONLY find patients assigned to them.
        # If they guess an ID of a patient assigned to someone else, 404 is returned.
        patient = get_object_or_404(Patient, patient_id=patient_id, assigned_clinician=request.user)
    else:
        # Admins can see any patient
        patient = get_object_or_404(Patient, patient_id=patient_id)

    latest_prediction = patient.predictions.order_by('-prediction_date').first()
    shap_data_json = json.dumps(latest_prediction.shap_values) if latest_prediction and latest_prediction.shap_values else '{}'
    recommendations = get_clinical_recommendations(latest_prediction.risk_category) if latest_prediction else []
        
    context = {
        'patient': patient,
        'prediction': latest_prediction,
        'shap_data_json': shap_data_json,
        'recommendations': recommendations,
    }
    return render(request, 'dashboard/patient_dashboard.html', context)

@login_required
@user_passes_test(is_clinician_or_admin)
def generate_prediction(request, patient_id):
    if request.method != 'POST':
        return redirect('patient_dashboard', patient_id=patient_id)

    # Scoping check using the 'Solid' lookup pattern
    if request.user.role == 'CLINICIAN':
        patient = get_object_or_404(Patient, patient_id=patient_id, assigned_clinician=request.user)
    else:
        patient = get_object_or_404(Patient, patient_id=patient_id)

    try:
        from ml_engine.predict import predict_ptld_risk
        risk_score, risk_category, model_used, shap_values = predict_ptld_risk(patient)

        Prediction.objects.create(
            patient_id=patient, risk_score=risk_score, risk_category=risk_category,
            model_used=model_used, shap_values=shap_values, triggered_by=request.user.username
        )
        messages.success(request, f'Prediction generated: {risk_category} risk.')
    except Exception as e:
        logger.error(f'Prediction failed: {e}')
        messages.error(request, f'Prediction failed: {e}')

    return redirect('patient_dashboard', patient_id=patient_id)
