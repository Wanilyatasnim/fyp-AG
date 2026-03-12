import os

file_path = r'c:\Users\Boyak\Desktop\fyp\fyp\fyp.AG\TodoList_TB_PTLD_utf8.txt'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

patterns = [
    # Section 1 Setup
    'Create GitHub repository', 'Set up .gitignore', 'Create Python virtual environment',
    'Install all dependencies', 'Create .env file', 'python-dotenv',
    'Run django-admin', 'Configure settings.py', 'Configure Django to use Supabase',
    
    # Section 2 DB
    'Create Patient model with all 38 dataset',
    'Add all 7 comorbidity fields to Patient',
    'Add HIV status', 'Add created_by', 'Create Treatment model',
    'Add baseline bacteriology fields', 'Add all 7 drug susceptibility',
    'Create MonitoringVisit model', 'Create Prediction model',
    "Extend Django's AbstractUser", 'Confirm JSONB type', 'Run makemigrations',
    
    # Section 3 Auth
    'Build login view', 'Redirect to role', 'Implement secure logout', 'Implement Role-Based',
    'Admin can create new user accounts', 'Admin can deactivate user accounts',
    
    # Section 4 Patient CRUD
    'Build patient registration form', 'Add clinical fields to registration',
    'Add all 7 comorbidity checkboxes', 'Add occupational_disease and state',
    'Auto-generate unique patient_id', 'Display confirmation with patient ID',
    'Build patient search', 'Build paginated patient list view',
    'Build patient update form', 'Implement PDF export', 'Implement CSV export',
    
    # Section 5, 6, 7 (ML done externally or in ml_engine)
    'Load Brazil TB 2019 dataset', 'Identify and document all columns with value 9',
    'Replace value 9 with NaN', 'Apply mode imputation',
    'Univariate analysis', 'Bivariate analysis', 'Serial bacilloscopy analysis',
    'Drug resistance analysis', 'Comorbidity co-occurrence matrix',
    'Create Drug_Resistance_Count', 'Create Comorbidity_Count',
    'Create Persistent_Positive_Months', 'Create Bacilloscopy_Clearance_Rate',
    'Create Disease_Severity_Score', 'Create Age_Risk_Category',
    'Save cleaned + feature-engineered dataset',
    'target variable', 'Stratified train/val/test split',
    'Apply SMOTE', 'Apply StandardScaler',
    'Train Logistic Regression', 'Train Random Forest', 'Train XGBoost',
    'Evaluate all 3 models', 'Generate confusion matrices', 'Select best model',
    'Serialise all 3 trained models', 'Save preprocessing pipeline', 'Place .pkl files',
    
    # Integrated in ml_engine
    'Load all 3 .pkl models', 'predict_ptld_risk', 'Implement risk categorisation',
    'SHAP TreeExplainer', 'SHAP LinearExplainer', 'Extract top 5 features',
    'Store SHAP values as JSONB', 'Connect post_save signal', 'Auto-trigger prediction',
    
    # Dashboards (Module 4)
    'Build Patient Detail page', 'Implement semi-circle risk gauge',
    'Build 6-month serial bacilloscopy trend chart',
    'Display SHAP Risk Explanation card', 'Display Recommendations card',
    'Build Population Dashboard page', 'Build 3 stat cards',
    'Build Monthly Risk Trends chart', 'Build Population Risk Drivers',
    'Build SHAP waterfall plot using Plotly', 'Demographic Distribution donut chart',
    
    # UI Screens
    'Login page — centred card', 'Patient Management List',
    'Add Patient form — multi-section', 'Edit Patient form',
    'Patient Detail page — identity card'
]

new_lines = []
for line in lines:
    checked = False
    for pat in patterns:
        if pat in line:
            new_lines.append(line.replace('☐', '☑'))
            checked = True
            break
    if not checked:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
