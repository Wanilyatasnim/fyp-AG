"""
TB-PTLD Model Training Script
===============================
Trains 3 models on the cleaned dataset:
  1. Logistic Regression
  2. Random Forest
  3. XGBoost

Output: ml_engine/models/*.pkl files
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, f1_score, recall_score,
    confusion_matrix, classification_report
)
from imblearn.over_sampling import SMOTE
import xgboost as xgb

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
]
TARGET_COL = 'Target'   # 1=Low Risk (cure), 0=High Risk (death/failure)

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
print("Loading cleaned dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Shape: {df.shape}")

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
# 3. SMOTE  (only on training set)
# ─────────────────────────────────────────────────────────────────────────────
print("\nApplying SMOTE to training set...")
smote = SMOTE(random_state=RANDOM_STATE)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
print(f"Post-SMOTE train size: {len(X_train_sm)} (High-Risk: {(y_train_sm==0).sum()})")

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
scale_pos = (y_train_sm == 1).sum() / (y_train_sm == 0).sum()
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
# 6. EVALUATION on VALIDATION SET
# ─────────────────────────────────────────────────────────────────────────────
print("\n─── Validation Results ───")
best_model_name = None
best_recall = 0

for name, res in results.items():
    recall = recall_score(y_val, res['val_pred'], pos_label=0)
    f1     = f1_score(y_val, res['val_pred'], pos_label=0)
    auc    = roc_auc_score(y_val, res['val_proba'])
    print(f"\n{name}:")
    print(f"  Recall (High-Risk): {recall:.4f}  |  F1: {f1:.4f}  |  AUC-ROC: {auc:.4f}")
    if recall > best_recall:
        best_recall = recall
        best_model_name = name

print(f"\n★  Best model by Recall: {best_model_name} ({best_recall:.4f})")

# Save feature column list for inference
joblib.dump(FEATURE_COLS, MODELS_DIR / 'feature_cols.pkl')
print(f"\nAll models saved to: {MODELS_DIR}")
print("Training complete!")
