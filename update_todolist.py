import sys, re
file_path = r'c:\Users\Boyak\Desktop\fyp\fyp\fyp.AG\TodoList_TB_PTLD.txt'
with open(file_path, 'r', encoding='utf-16le') as f:
    lines = f.readlines()

patterns = [
    # Section 1 Setup
    "Create GitHub repository", "Set up .gitignore", "Create Python virtual environment",
    "Install all dependencies", "Create .env file", "python-dotenv",
    "Run django-admin", "Configure settings.py", "Configure Django to use Supabase",
    
    # Section 2 DB
    "Create Patient model with all 38 dataset",
    "Add all 7 comorbidity fields to Patient",
    "Add HIV status", "Add created_by", "Create Treatment model",
    "Add baseline bacteriology fields", "Add all 7 drug susceptibility",
    "Create MonitoringVisit model", "Create Prediction model",
    "Extend Django's AbstractUser", "Create AuditLog model", "Run makemigrations",
    "Confirm JSONB type",
    
    # Section 3 Auth
    "Build login view", "Redirect to role", "Implement secure logout", "Implement Role-Based",
    
    # Section 4 Patient CRUD
    "Build patient registration form", "Add clinical fields to registration",
    "Add all 7 comorbidity checkboxes to registration form",
    "Add occupational_disease and state to registration form",
    "Auto-generate unique patient_id",
    "Display confirmation with patient ID",
    "Build patient search",
    "Build paginated patient list view",
    
    # Section 5,6,7 ML
    "Load Brazil TB 2019 dataset", "Identify and document all columns with value 9",
    "Replace value 9 with NaN", "Apply mode imputation",
    "Define target variable:", "Stratified train/val/test split:",
    "Apply SMOTE oversampling", "Apply StandardScaler",
    "Train Logistic Regression", "Train Random Forest", "Train XGBoost",
    "Evaluate all 3 models", "Generate confusion matrices", "Select best model",
    "Serialise all 3 trained models", "Save preprocessing pipeline", "Place .pkl files",
    "Load all 3 .pkl models", "predict_ptld_risk", "Implement risk categorisation",
    "SHAP TreeExplainer", "SHAP LinearExplainer", "Extract top 5 features",
    "Store SHAP values as JSONB", "Connect post_save signal", "Auto-trigger prediction",
    
    # Section 8 Dashboard
    "Build Patient Detail page:", "Implement semi-circle risk gauge",
    "Build 6-month serial bacilloscopy trend chart",
    "Display SHAP Risk Explanation card:", "Display Recommendations card:",
    "Build Population Dashboard page", "Build 3 stat cards",
    "Build Monthly Risk Trends chart", "Build Population Risk Drivers",
    "Build SHAP waterfall plot using Plotly", "Build Demographic Distribution",
    
    # Section 9 UI
    "Login page — centred card", "Patient Management List", "Add Patient form",
    "Patient Detail page — identity card", "Define --color-risk-low:"
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

with open(file_path, 'w', encoding='utf-16le') as f:
    f.writelines(new_lines)
