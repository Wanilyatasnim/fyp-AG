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
    'MDR_TB', 'Persistent_Positive', 'Treatment_Failing',
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
    
    mdr_tb = 1 if (tv('Rifampicin', 3) == 2 and tv('Isoniazid', 3) == 2) else 0
    persistent_pos_flag = 1 if any(tv(f'Bacilloscopy_Month_{i}', 3) == 1 for i in [4, 5, 6]) else 0
    treatment_failing = 1 if (mdr_tb == 1 and persistent_pos_flag == 1) else 0

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
        tv('Days_In_Treatment', 0) or 0,
        age_val,
        drug_resistance_count,
        comorbidity_count,
        persistent_positive,
        clearance_rate,
        disease_severity_score,
        age_risk,
        mdr_tb,
        persistent_pos_flag,
        treatment_failing,
    ]
    return np.array(row).reshape(1, -1)


def _load_model(name):
    import joblib
    path = MODELS_DIR / f'{name}.pkl'
    if path.exists():
        try:
            model = joblib.load(path)
            # Compatibility patch for sklearn 1.5.2 -> 1.7.2 unpickling issues
            if name == 'logistic_regression' and not hasattr(model, 'multi_class'):
                model.multi_class = 'ovr'
            return model
        except Exception:
            return None
    return None


def apply_clinical_override(ml_score, patient):
    try:
        t = patient.treatment
    except Exception:
        t = None
        
    def tv(field, default=3):
        return getattr(t, field, default)
        
    rif = tv('Rifampicin', 3)
    iso = tv('Isoniazid', 3)
    aids = getattr(patient, 'AIDS_Comorbidity', 2)
    sputum_m3 = tv('Bacilloscopy_Month_3', 3)
    sputum_m4 = tv('Bacilloscopy_Month_4', 3)
    
    # Rule 1 — MDR-TB + sputum still positive at month 4
    if rif == 2 and iso == 2 and sputum_m4 == 1:
        ml_score = max(ml_score, 0.75)
        
    # Rule 2 — AIDS + sputum positive beyond month 3
    if aids == 1 and sputum_m3 == 1:
        ml_score = max(ml_score, 0.60)
        
    # Rule 3 — All 6 months sputum positive
    months = [tv(f'Bacilloscopy_Month_{i}', 3) for i in range(1, 7)]
    if all(m == 1 for m in months):
        ml_score = max(ml_score, 0.70)
        
    return ml_score


def predict_ptld_risk(patient):
    """
    Run PTLD risk prediction for a Patient instance using a Mean Probability Ensemble.
    Combines outputs from Logistic Regression, Random Forest, and XGBoost.
    """
    scaler  = _load_model('scaler')
    xgb_m   = _load_model('xgboost')
    rf_m    = _load_model('random_forest')
    lr_m    = _load_model('logistic_regression')

    feature_vec = _extract_features(patient)
    
    available_probas = []
    used_models = []

    # 1. XGBoost
    if xgb_m is not None:
        proba = xgb_m.predict_proba(feature_vec)[0]
        # proba[0] = High Risk (label 0), proba[1] = Low Risk (label 1)
        available_probas.append(float(proba[0]))
        used_models.append("XGB")

    # 2. Random Forest
    if rf_m is not None:
        proba = rf_m.predict_proba(feature_vec)[0]
        available_probas.append(float(proba[0]))
        used_models.append("RF")

    # 3. Logistic Regression (requires scaled features)
    if lr_m is not None and scaler is not None:
        scaled_features = scaler.transform(feature_vec)
        proba = lr_m.predict_proba(scaled_features)[0]
        available_probas.append(float(proba[0]))
        used_models.append("LR")

    # Handle fallback if no models exist
    if not available_probas:
        model_name = 'Placeholder (not trained)'
        risk_score = random.uniform(0, 1)
        category   = 'Low' if risk_score <= 0.33 else ('Moderate' if risk_score <= 0.67 else 'High')
        shap_values = {f: round(random.uniform(-0.3, 0.3), 3) for f in FEATURE_COLS[:5]}
        return risk_score, category, model_name, shap_values

    # Calculate Ensemble Mean Probability
    high_risk_score = sum(available_probas) / len(available_probas)
    
    # Apply Clinical Override
    high_risk_score = apply_clinical_override(high_risk_score, patient)
    
    # Build dynamic model label
    if len(used_models) > 1:
        model_name = f"Ensemble ({' + '.join(used_models)})"
    else:
        model_name = f"{used_models[0]} (trained)"

    if high_risk_score <= 0.33:
        category = 'Low'
    elif high_risk_score <= 0.67:
        category = 'Moderate'
    else:
        category = 'High'

    # Best single model for SHAP (Priority: XGB -> RF -> LR)
    model_for_shap = xgb_m or rf_m or lr_m

    # SHAP values
    shap_values = {}
    try:
        import shap
        if xgb_m is not None:
            explainer = shap.TreeExplainer(model_for_shap)
            sv = explainer.shap_values(feature_vec)[0]
        elif rf_m is not None:
            explainer = shap.TreeExplainer(model_for_shap)
            sv = explainer.shap_values(feature_vec)[0]
        elif lr_m is not None and scaler is not None:
            scaled_features = scaler.transform(feature_vec)
            explainer = shap.LinearExplainer(model_for_shap, masker=shap.maskers.Independent(scaled_features))
            sv = explainer.shap_values(scaled_features)[0]
        else:
            sv = None

        if sv is not None:
            # Return ALL features and their SHAP values to the frontend for categorization
            shap_values = {feat: round(float(val), 4) for feat, val in zip(FEATURE_COLS, sv)}
        else:
            # Default empty values if SHAP fails
            shap_values = {f: 0.0 for f in FEATURE_COLS}
    except Exception:
        shap_values = {f: 0.0 for f in FEATURE_COLS}

    return high_risk_score, category, model_name, shap_values
