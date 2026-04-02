from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

def is_clinician_or_admin(user):
    return user.is_authenticated and user.role in ['ADMIN', 'CLINICIAN']
from django.contrib import messages
from django.db.models import Avg
from patients.models import Patient
from ml_engine.models import Prediction
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def population_dashboard(request):
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
def patient_dashboard(request, patient_id):
    """
    Renders the detailed dashboard for a single patient, including SHAP values.
    """
    patient = get_object_or_404(Patient, patient_id=patient_id)
    latest_prediction = patient.predictions.order_by('-prediction_date').first()
    
    # Serialize SHAP values for JS consumption
    shap_data_json = '{}'
    if latest_prediction and latest_prediction.shap_values:
        shap_data_json = json.dumps(latest_prediction.shap_values)
        
    context = {
        'patient': patient,
        'prediction': latest_prediction,
        'shap_data_json': shap_data_json,
    }
    return render(request, 'dashboard/patient_dashboard.html', context)


@login_required
@user_passes_test(is_clinician_or_admin)
def generate_prediction(request, patient_id):
    """
    Manual trigger for clinician: run prediction and save to DB.
    Only allows POST to prevent accidental GET triggers.
    """
    if request.method != 'POST':
        return redirect('patient_dashboard', patient_id=patient_id)

    patient = get_object_or_404(Patient, patient_id=patient_id)

    try:
        from ml_engine.predict import predict_ptld_risk
        risk_score, risk_category, model_used, shap_values = predict_ptld_risk(patient)

        Prediction.objects.create(
            patient_id=patient,
            risk_score=risk_score,
            risk_category=risk_category,
            model_used=model_used,
            shap_values=shap_values,
            triggered_by=request.user,
        )
        messages.success(
            request,
            f'Prediction generated: {risk_category} risk (score {round(risk_score*100, 1)}%).'
        )
    except Exception as e:
        logger.error(f'Manual prediction failed for {patient_id}: {e}')
        messages.error(request, f'Prediction failed: {e}')

    return redirect('patient_dashboard', patient_id=patient_id)
