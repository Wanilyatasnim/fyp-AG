"""
ml_engine/predict.py
Loads the best trained .pkl model and runs PTLD risk prediction.
Falls back to a dummy model if .pkl files are not yet available.
"""
import os
import json
import random
import numpy as np
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / 'models'

# Feature columns must match train_models.py exactly
FEATURE_COLS = [
    'Sex', 'Race', 'Treatment', 'Chest_X_Ray', 'Clinical_Form',
    'AIDS_Comorbidity', 'Alcoholism_Comorbidity', 'Diabetes_Comorbidity',
    'Mental_Disorder_Comorbidity', 'Other_Comorbidity',
    'Drug_Addiction_Comorbidity', 'Smoking_Comorbidity',
    'Bacilloscopy_Sputum', 'Bacilloscopy_Sputum_2', 'Bacilloscopy_Other',
    'Sputum_Culture', 'HIV', 'Occupational_Disease',
    'Rifampicin', 'Isoniazid', 'Ethambutol', 'Streptomycin',
    'Pyrazinamide', 'Ethionamide', 'Other_Drugs',
    'Supervised_Treatment',
    'Bacilloscopy_Month_1', 'Bacilloscopy_Month_2', 'Bacilloscopy_Month_3',
    'Bacilloscopy_Month_4', 'Bacilloscopy_Month_5', 'Bacilloscopy_Month_6',
    'Days_In_Treatment', 'Age',
    'Drug_Resistance_Count', 'Comorbidity_Count', 'Persistent_Positive_Months',
    'Bacilloscopy_Clearance_Rate', 'Disease_Severity_Score', 'Age_Risk_Category',
]


def _extract_features(patient):
    """
    Extract feature vector from a Patient model instance.
    Maps Django model field names → dataset column names.
    """
    from treatments.models import Treatment as TreatmentModel

    try:
        treatment = patient.treatment
    except Exception:
        treatment = None

    def tv(field, default=None):
        """Get Treatment field value."""
        return getattr(treatment, field, default)

    drug_cols = ['Rifampicin', 'Isoniazid', 'Ethambutol', 'Streptomycin',
                 'Pyrazinamide', 'Ethionamide', 'Other_Drugs']
    comorbidity_cols = ['AIDS_Comorbidity', 'Alcoholism_Comorbidity', 'Diabetes_Comorbidity',
                        'Mental_Disorder_Comorbidity', 'Drug_Addiction_Comorbidity',
                        'Smoking_Comorbidity', 'Other_Comorbidity']
    bacillo_months = ['Bacilloscopy_Month_1', 'Bacilloscopy_Month_2', 'Bacilloscopy_Month_3',
                      'Bacilloscopy_Month_4', 'Bacilloscopy_Month_5', 'Bacilloscopy_Month_6']

    drug_values = [tv(d, 3) or 3 for d in drug_cols]
    comorbidity_values = [getattr(patient, c, 2) or 2 for c in comorbidity_cols]
    month_values = [tv(m, 3) or 3 for m in bacillo_months]

    drug_resistance_count    = sum(1 for v in drug_values if v == 2)
    comorbidity_count        = sum(1 for v in comorbidity_values if v == 1)
    persistent_positive      = sum(1 for v in month_values if v == 1)
    clearance_rate           = (month_values[5] if month_values[5] != 3 else 2) - (month_values[0] if month_values[0] != 3 else 2)
    chest_val                = patient.Chest_X_Ray or 2
    bac_sputum_val           = tv('Bacilloscopy_Sputum', 2) or 2
    disease_severity_score   = chest_val + bac_sputum_val
    age_val                  = patient.Age or 30
    if age_val <= 14:
        age_risk = 0
    elif age_val <= 45:
        age_risk = 1
    elif age_val <= 65:
        age_risk = 2
    else:
        age_risk = 3

    row = [
        patient.Sex or 1,
        patient.Race or 1,
        patient.Treatment or 1,
        chest_val,
        patient.Clinical_Form or 1,
        getattr(patient, 'AIDS_Comorbidity', 2) or 2,
        getattr(patient, 'Alcoholism_Comorbidity', 2) or 2,
        getattr(patient, 'Diabetes_Comorbidity', 2) or 2,
        getattr(patient, 'Mental_Disorder_Comorbidity', 2) or 2,
        getattr(patient, 'Other_Comorbidity', 2) or 2,
        getattr(patient, 'Drug_Addiction_Comorbidity', 2) or 2,
        getattr(patient, 'Smoking_Comorbidity', 2) or 2,
        bac_sputum_val,
        tv('Bacilloscopy_Sputum_2', 3) or 3,
        tv('Bacilloscopy_Other', 3) or 3,
        tv('Sputum_Culture', 3) or 3,
        patient.HIV or 4,
        getattr(patient, 'Occupational_Disease', 2) or 2,
        *drug_values,
        tv('Supervised_Treatment', 1) or 1,
        *month_values,
        tv('Days_In_Treatment', 180) or 180,
        age_val,
        drug_resistance_count,
        comorbidity_count,
        persistent_positive,
        clearance_rate,
        disease_severity_score,
        age_risk,
    ]
    return np.array(row).reshape(1, -1)


def _load_model(name):
    import joblib
    path = MODELS_DIR / f'{name}.pkl'
    if path.exists():
        return joblib.load(path)
    return None


def predict_ptld_risk(patient):
    """
    Run PTLD risk prediction for a Patient instance.
    Returns: (risk_score, risk_category, model_used, shap_values)
    """
    scaler  = _load_model('scaler')
    xgb_m   = _load_model('xgboost')
    rf_m    = _load_model('random_forest')
    lr_m    = _load_model('logistic_regression')

    feature_vec = _extract_features(patient)

    # Priority: XGBoost → RF → LR → Dummy
    if xgb_m is not None:
        model      = xgb_m
        model_name = 'XGBoost (trained)'
        proba      = model.predict_proba(feature_vec)[0]
    elif rf_m is not None:
        model      = rf_m
        model_name = 'Random Forest (trained)'
        proba      = model.predict_proba(feature_vec)[0]
    elif lr_m is not None and scaler is not None:
        model      = lr_m
        model_name = 'Logistic Regression (trained)'
        proba      = model.predict_proba(scaler.transform(feature_vec))[0]
    else:
        # Dummy fallback until training is done
        model_name = 'Placeholder (not trained)'
        risk_score = random.uniform(0, 1)
        category   = 'Low' if risk_score <= 0.33 else ('Moderate' if risk_score <= 0.67 else 'High')
        shap_values = {f: round(random.uniform(-0.3, 0.3), 3) for f in FEATURE_COLS[:5]}
        return risk_score, category, model_name, shap_values

    # proba[0] = High Risk (label 0), proba[1] = Low Risk (label 1)
    high_risk_score = float(proba[0])

    if high_risk_score <= 0.33:
        category = 'Low'
    elif high_risk_score <= 0.67:
        category = 'Moderate'
    else:
        category = 'High'

    # SHAP values
    shap_values = {}
    try:
        import shap
        if xgb_m is not None:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(feature_vec)[0]
        elif rf_m is not None:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(feature_vec)[0]
        else:
            explainer = shap.LinearExplainer(model, masker=shap.maskers.Independent(feature_vec))
            sv = explainer.shap_values(feature_vec)[0]
        # Top 5 by absolute contribution
        top5 = sorted(zip(FEATURE_COLS, sv), key=lambda x: abs(x[1]), reverse=True)[:5]
        shap_values = {k: round(float(v), 4) for k, v in top5}
    except Exception:
        shap_values = {f: 0.0 for f in FEATURE_COLS[:5]}

    return high_risk_score, category, model_name, shap_values
