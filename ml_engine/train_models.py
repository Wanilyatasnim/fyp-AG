"""
TB-PTLD Model Training Script
===============================
Trains 3 models on the cleaned dataset:
  1. Logistic Regression
  2. Random Forest
  3. XGBoost

Output: ml_engine/models/*.pkl files
"""

import xgboost as xgb
import shap
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import joblib

# ── Django Setup ──
import os
import django
import sys

# Set up Django environment so we can save to models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tbptld.settings')
django.setup()

from ml_engine.models import ModelMetric
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DATA_PATH   = Path("C:/Users/Boyak/Desktop/fyp/fyp/data/tb_ptld_cleaned.csv")
MODELS_DIR  = Path("C:/Users/Boyak/Desktop/fyp/fyp/fyp.AG/ml_engine/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42

# Feature columns  (dataset cols + engineered features)
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
    # Engineered features
    'Drug_Resistance_Count', 'Comorbidity_Count', 'Persistent_Positive_Months',
    'Bacilloscopy_Clearance_Rate', 'Disease_Severity_Score', 'Age_Risk_Category',
    'MDR_TB', 'Persistent_Positive', 'Treatment_Failing',
]
TARGET_COL = 'Target'   # 1=Low Risk (cure), 0=High Risk (death/failure)

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
print("Loading cleaned dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Shape: {df.shape}")

# Inject 100 Synthetic MDR-TB Failure rows
import numpy as np
real_failures = df[(df['MDR_TB'] == 1) & (df['Target'] == 0)]
if not real_failures.empty:
    print(f"Synthesizing 100 MDR-TB failures from {len(real_failures)} base cases...")
    synth_list = []
    for _ in range(100):
        base = real_failures.sample(n=1).copy()
        base['Age'] = base['Age'] + np.random.randint(-5, 6)
        base['Age'] = base['Age'].clip(lower=1)
        age = base['Age'].iloc[0]
        base['Age_Risk_Category'] = 0 if age <= 14 else (1 if age <= 45 else (2 if age <= 65 else 3))
        synth_list.append(base)
    df = pd.concat([df] + synth_list, ignore_index=True)
    print(f"Shape after injection: {df.shape}")

X = df[FEATURE_COLS].fillna(df[FEATURE_COLS].median())
y = df[TARGET_COL]

# ─────────────────────────────────────────────────────────────────────────────
# 2. TRAIN / VAL / TEST SPLIT  (70 / 15 / 15)
# ─────────────────────────────────────────────────────────────────────────────
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y, test_size=0.15, stratify=y, random_state=RANDOM_STATE
)
X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval, test_size=0.15 / 0.85, stratify=y_trainval, random_state=RANDOM_STATE
)
print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
print(f"High-Risk in train: {(y_train==0).sum()} / {len(y_train)}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. SMOTE  (Removed according to fix plan)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSkipping SMOTE. Using real data with class weights.")
X_train_sm = X_train
y_train_sm = y_train

# ─────────────────────────────────────────────────────────────────────────────
# 4. PREPROCESSING
# ─────────────────────────────────────────────────────────────────────────────
scaler = StandardScaler()
X_train_lr = scaler.fit_transform(X_train_sm)
X_val_lr   = scaler.transform(X_val)
X_test_lr  = scaler.transform(X_test)

joblib.dump(scaler, MODELS_DIR / 'scaler.pkl')
print("Scaler saved.")

# ─────────────────────────────────────────────────────────────────────────────
# 5. TRAIN MODELS
# ─────────────────────────────────────────────────────────────────────────────
results = {}

# ── Logistic Regression ──
print("\nTraining Logistic Regression...")
lr_params = {'C': [0.01, 0.1, 1, 10], 'solver': ['lbfgs'], 'max_iter': [1000]}
lr = GridSearchCV(
    LogisticRegression(class_weight='balanced', random_state=RANDOM_STATE),
    lr_params, cv=5, scoring='recall', n_jobs=-1, verbose=0
)
lr.fit(X_train_lr, y_train_sm)
best_lr = lr.best_estimator_
joblib.dump(best_lr, MODELS_DIR / 'logistic_regression.pkl')
results['LogisticRegression'] = {
    'model': best_lr,
    'val_pred': best_lr.predict(X_val_lr),
    'val_proba': best_lr.predict_proba(X_val_lr)[:, 0],  # proba of High Risk (0)
}
print(f"  Best params: {lr.best_params_}")

# ── Random Forest ──
print("\nTraining Random Forest...")
rf_params = {'n_estimators': [100, 200], 'max_depth': [None, 10, 20], 'min_samples_split': [2, 5]}
rf = GridSearchCV(
    RandomForestClassifier(class_weight='balanced', random_state=RANDOM_STATE),
    rf_params, cv=5, scoring='recall', n_jobs=-1, verbose=0
)
rf.fit(X_train_sm, y_train_sm)
best_rf = rf.best_estimator_
joblib.dump(best_rf, MODELS_DIR / 'random_forest.pkl')
results['RandomForest'] = {
    'model': best_rf,
    'val_pred': best_rf.predict(X_val),
    'val_proba': best_rf.predict_proba(X_val)[:, 0],
}
print(f"  Best params: {rf.best_params_}")

# ── XGBoost ──
print("\nTraining XGBoost...")
scale_pos = (y_train_sm == 0).sum() / (y_train_sm == 1).sum()
xgb_params = {
    'n_estimators': [100, 200],
    'max_depth': [3, 6],
    'learning_rate': [0.05, 0.1],
}
xgb_model = GridSearchCV(
    xgb.XGBClassifier(
        scale_pos_weight=scale_pos, eval_metric='logloss',
        random_state=RANDOM_STATE, use_label_encoder=False, verbosity=0
    ),
    xgb_params, cv=5, scoring='recall', n_jobs=-1, verbose=0
)
xgb_model.fit(X_train_sm, y_train_sm)
best_xgb = xgb_model.best_estimator_
joblib.dump(best_xgb, MODELS_DIR / 'xgboost.pkl')
results['XGBoost'] = {
    'model': best_xgb,
    'val_pred': best_xgb.predict(X_val),
    'val_proba': best_xgb.predict_proba(X_val)[:, 0],
}
print(f"  Best params: {xgb_model.best_params_}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. EVALUATION on VALIDATION SET + TEST SET
# ─────────────────────────────────────────────────────────────────────────────
print("\n─── Validation Results ───")
best_model_name = None
best_recall = 0

for name, res in results.items():
    acc    = accuracy_score(y_val, res['val_pred'])
    prec   = precision_score(y_val, res['val_pred'], pos_label=0, zero_division=0)
    recall = recall_score(y_val, res['val_pred'], pos_label=0, zero_division=0)
    f1     = f1_score(y_val, res['val_pred'], pos_label=0, zero_division=0)
    auc    = roc_auc_score(y_val, res['val_proba'])
    cm     = confusion_matrix(y_val, res['val_pred'])
    print(f"\n{name}:")
    print(f"  Accuracy: {acc:.4f}  |  Precision: {prec:.4f}  |  Recall (High-Risk): {recall:.4f}  |  F1: {f1:.4f}  |  AUC-ROC: {auc:.4f}")
    print(f"  Confusion Matrix:\n{cm}")
    res['val_metrics'] = dict(accuracy=acc, precision=prec, recall=recall, f1=f1, auc=auc)
    if recall > best_recall:
        best_recall = recall
        best_model_name = name

print(f"\n★  Best model by Recall: {best_model_name} ({best_recall:.4f})")

# ─── Test Set Evaluation ───
print("\n─── Test Set Results (Held-Out) ───")
for name, res in results.items():
    model = res['model']
    if name == 'LogisticRegression':
        X_test_input = X_test_lr
    else:
        X_test_input = X_test

    test_pred  = model.predict(X_test_input)
    test_proba = model.predict_proba(X_test_input)[:, 0]  # proba of High Risk (0)
    acc    = accuracy_score(y_test, test_pred)
    prec   = precision_score(y_test, test_pred, pos_label=0, zero_division=0)
    recall = recall_score(y_test, test_pred, pos_label=0, zero_division=0)
    f1     = f1_score(y_test, test_pred, pos_label=0, zero_division=0)
    auc    = roc_auc_score(y_test, test_proba)
    cm     = confusion_matrix(y_test, test_pred)
    print(f"\n{name} [TEST]:")
    print(f"  Accuracy: {acc:.4f}  |  Precision: {prec:.4f}  |  Recall: {recall:.4f}  |  F1: {f1:.4f}  |  AUC-ROC: {auc:.4f}")
    print(f"  Confusion Matrix:\n{cm}")
    res['test_metrics'] = dict(accuracy=acc, precision=prec, recall=recall, f1=f1, auc=auc)

# ─────────────────────────────────────────────────────────────────────────────
# 7. SAVE METRICS TO DATABASE  (all 3 models)
# ─────────────────────────────────────────────────────────────────────────────
print("\nSaving metrics for all models to database...")

# Delete old auto-saved entries so there are no duplicates across retrains
ModelMetric.objects.filter(version="1.1.0 (Auto)").delete()

# Global SHAP for best model only (TreeExplainer can be slow)
print("Calculating global SHAP values for best model...")
best_res = results[best_model_name]
explainer = shap.TreeExplainer(best_res['model'])
if best_model_name == 'LogisticRegression':
    shap_input = X_val_lr
else:
    shap_input = X_val
shap_vals = explainer.shap_values(shap_input)
if isinstance(shap_vals, list):
    shap_vals = shap_vals[0]
global_importance = {
    col: float(np.abs(shap_vals[:, i]).mean())
    for i, col in enumerate(FEATURE_COLS)
}

for name, res in results.items():
    m = res['test_metrics']  # use test-set scores for the DB record
    is_best = (name == best_model_name)
    ModelMetric.objects.create(
        version="1.1.0 (Auto)",
        model_name=name,
        accuracy=m['accuracy'],
        precision=m['precision'],
        recall=m['recall'],
        f1_score=m['f1'],
        auc_roc=m['auc'],
        # Only store SHAP for best model; empty dict for others
        global_importance=global_importance if is_best else {}
    )
    print(f"  Saved metrics for {name}")

# Save feature column list for inference
joblib.dump(FEATURE_COLS, MODELS_DIR / 'feature_cols.pkl')
print(f"\nAll models and metrics saved.")
print("Training complete!")
