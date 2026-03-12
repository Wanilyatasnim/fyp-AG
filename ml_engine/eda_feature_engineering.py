"""
TB-PTLD EDA & Feature Engineering Script
=========================================
Run this script (or as a Jupyter Notebook) to:
  1. Load and clean the Brazil TB 2019 dataset
  2. Perform EDA (univariate + bivariate analysis)
  3. Engineer new features
  4. Save cleaned dataset for model training

Dataset: brazil_tb_2019_last20k_english.xlsx
Output:  data/tb_ptld_cleaned.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DATA_PATH   = Path("C:/Users/Boyak/Desktop/fyp/fyp/data/brazil_tb_2019_last20k_english.xlsx")
OUTPUT_PATH = Path("C:/Users/Boyak/Desktop/fyp/fyp/data/tb_ptld_cleaned.csv")

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD
# ─────────────────────────────────────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_excel(DATA_PATH)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. HANDLE MISSING VALUES
# Value 9 = Unknown / Not applicable → treat as NaN
# ─────────────────────────────────────────────────────────────────────────────
COLS_WITH_9_AS_MISSING = [
    'Sex', 'Race', 'Treatment', 'Chest_X_Ray', 'Clinical_Form',
    'AIDS_Comorbidity', 'Alcoholism_Comorbidity', 'Diabetes_Comorbidity',
    'Mental_Disorder_Comorbidity', 'Other_Comorbidity',
    'Drug_Addiction_Comorbidity', 'Smoking_Comorbidity',
    'Bacilloscopy_Sputum', 'Bacilloscopy_Sputum_2', 'Bacilloscopy_Other',
    'Sputum_Culture', 'HIV',
    'Rifampicin', 'Isoniazid', 'Ethambutol', 'Streptomycin',
    'Pyrazinamide', 'Ethionamide', 'Other_Drugs',
    'Supervised_Treatment', 'Occupational_Disease',
    'Bacilloscopy_Month_1', 'Bacilloscopy_Month_2', 'Bacilloscopy_Month_3',
    'Bacilloscopy_Month_4', 'Bacilloscopy_Month_5', 'Bacilloscopy_Month_6',
]
for col in COLS_WITH_9_AS_MISSING:
    if col in df.columns:
        df[col] = df[col].replace(9, np.nan)

print(f"\nMissing values after replacing 9s:\n{df.isnull().sum()[df.isnull().sum() > 0]}")

# Imputation: mode for categoricals, median for numerics
for col in COLS_WITH_9_AS_MISSING:
    if col in df.columns and df[col].isnull().any():
        df[col].fillna(df[col].mode()[0], inplace=True)

if df['Age'].isnull().any():
    df['Age'].fillna(df['Age'].median(), inplace=True)

if 'Days_In_Treatment' in df.columns and df['Days_In_Treatment'].isnull().any():
    df['Days_In_Treatment'].fillna(df['Days_In_Treatment'].median(), inplace=True)

print(f"\nMissing values after imputation:\n{df.isnull().sum()[df.isnull().sum() > 0].to_string()}")
print("(Should be 0 for all imputed columns)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. UNIVARIATE EDA
# ─────────────────────────────────────────────────────────────────────────────
print("\n─── Outcome_Status distribution ───")
print(df['Outcome_Status'].value_counts())
print(f"\nClass imbalance ratio: {df['Outcome_Status'].value_counts()[1]/df['Outcome_Status'].value_counts()[3]:.1f}:1 (Low:High)")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
df['Age'].hist(bins=30, ax=axes[0], color='steelblue', edgecolor='white')
axes[0].set_title('Age Distribution')
axes[0].set_xlabel('Age')

if 'Days_In_Treatment' in df.columns:
    df['Days_In_Treatment'].hist(bins=30, ax=axes[1], color='coral', edgecolor='white')
    axes[1].set_title('Days In Treatment Distribution')
    axes[1].set_xlabel('Days')

plt.tight_layout()
plt.savefig("C:/Users/Boyak/Desktop/fyp/fyp/data/eda_univariate.png", dpi=120)
plt.close()
print("Saved eda_univariate.png")

# ─────────────────────────────────────────────────────────────────────────────
# 4. BIVARIATE EDA
# ─────────────────────────────────────────────────────────────────────────────
from scipy import stats

cat_cols = [c for c in COLS_WITH_9_AS_MISSING if c in df.columns]
print("\n─── Chi-Square tests (vs Outcome_Status) ───")
sig_cols = []
for col in cat_cols:
    ct = pd.crosstab(df[col], df['Outcome_Status'])
    chi2, p, _, _ = stats.chi2_contingency(ct)
    if p < 0.05:
        sig_cols.append(col)
        print(f"  ✓ {col}: p={p:.4f}")

# Bacilloscopy clearance by risk group
bacillo_cols = [f'Bacilloscopy_Month_{i}' for i in range(1, 7)]
df_melted = df[['Outcome_Status'] + bacillo_cols].melt(
    id_vars='Outcome_Status', var_name='Month', value_name='Result'
)
plt.figure(figsize=(10, 5))
for outcome, label, color in [(1, 'Low Risk (Cure)', 'green'), (3, 'High Risk', 'red')]:
    sub = df_melted[df_melted['Outcome_Status'] == outcome]
    pos_pct = sub.groupby('Month')['Result'].apply(lambda x: (x == 1).mean() * 100)
    plt.plot(range(1, 7), pos_pct.values, label=label, color=color, marker='o')

plt.xlabel('Month')
plt.ylabel('% Positive Bacilloscopy')
plt.title('Serial Bacilloscopy Clearance by Outcome Group')
plt.legend()
plt.savefig("C:/Users/Boyak/Desktop/fyp/fyp/data/eda_bacilloscopy.png", dpi=120)
plt.close()
print("Saved eda_bacilloscopy.png")

# ─────────────────────────────────────────────────────────────────────────────
# 5. FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
drug_cols = ['Rifampicin', 'Isoniazid', 'Ethambutol', 'Streptomycin',
             'Pyrazinamide', 'Ethionamide', 'Other_Drugs']
comorbidity_cols = ['AIDS_Comorbidity', 'Alcoholism_Comorbidity', 'Diabetes_Comorbidity',
                    'Mental_Disorder_Comorbidity', 'Drug_Addiction_Comorbidity',
                    'Smoking_Comorbidity', 'Other_Comorbidity']

# Drug_Resistance_Count: count of resistant (value=2) drugs
df['Drug_Resistance_Count'] = df[drug_cols].apply(lambda row: (row == 2).sum(), axis=1)

# Comorbidity_Count: count of Yes (value=1) comorbidities
df['Comorbidity_Count'] = df[comorbidity_cols].apply(lambda row: (row == 1).sum(), axis=1)

# Persistent_Positive_Months: count of Positive (1) bacilloscopy months
df['Persistent_Positive_Months'] = df[bacillo_cols].apply(lambda row: (row == 1).sum(), axis=1)

# Bacilloscopy_Clearance_Rate: month6 - month1 (negative = improvement)
df['Bacilloscopy_Clearance_Rate'] = (
    df['Bacilloscopy_Month_6'].fillna(2) - df['Bacilloscopy_Month_1'].fillna(2)
)

# Disease_Severity_Score: composite of Chest X-Ray + Bacilloscopy_Sputum
df['Disease_Severity_Score'] = (
    df['Chest_X_Ray'].fillna(2) + df['Bacilloscopy_Sputum'].fillna(2)
)

# Age_Risk_Category: bins <15 / 15–45 / 46–65 / >65
df['Age_Risk_Category'] = pd.cut(
    df['Age'],
    bins=[0, 14, 45, 65, 200],
    labels=[0, 1, 2, 3],  # <15, 15-45, 46-65, >65
    right=True
).astype(float)

# Binary target: 1=Low Risk (Outcome_Status==1), 0=High Risk (Outcome_Status==3)
df['Target'] = (df['Outcome_Status'] == 1).astype(int)

print("\n─── Engineered Features ───")
eng_cols = ['Drug_Resistance_Count', 'Comorbidity_Count', 'Persistent_Positive_Months',
            'Bacilloscopy_Clearance_Rate', 'Disease_Severity_Score', 'Age_Risk_Category', 'Target']
print(df[eng_cols].describe())

# ─────────────────────────────────────────────────────────────────────────────
# 6. SAVE CLEANED DATASET
# ─────────────────────────────────────────────────────────────────────────────
df.to_csv(OUTPUT_PATH, index=False)
print(f"\nCleaned dataset saved to: {OUTPUT_PATH}")
print(f"Final shape: {df.shape}")
print(f"\nHigh-Risk samples: {(df['Target']==0).sum()} ({(df['Target']==0).mean()*100:.1f}%)")
print(f"Low-Risk samples:  {(df['Target']==1).sum()} ({(df['Target']==1).mean()*100:.1f}%)")
print("\nEDA complete!")
