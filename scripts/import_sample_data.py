"""
Script to import sample data from the cleaned CSV into the Django DB.
Imports the first 100 rows to avoid cluttering but show realistic data.
"""
import os
import django
import pandas as pd
from pathlib import Path

# Setup Django
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tbptld.settings')
django.setup()

from patients.models import Patient
from treatments.models import Treatment

DATA_PATH = Path("C:/Users/Boyak/Desktop/fyp/fyp/data/tb_ptld_cleaned.csv")

def run_import(limit=100):
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH).head(limit)
    df['Notification_Date'] = pd.to_datetime(df['Notification_Date'], dayfirst=True, errors='coerce')
    
    import math
    def clean(val):
        if val is None: return None
        try:
            if isinstance(val, (float, int)) and math.isnan(val):
                return None
        except: pass
        return val

    print(f"Importing {len(df)} records...")
    
    created_count = 0
    for _, row in df.iterrows():
        # Create Patient
        p = Patient.objects.create(
            name=f"Sample Patient {created_count + 1}",
            Notification_Date=clean(row.get('Notification_Date')),
            Sex=clean(row.get('Sex')),
            Race=clean(row.get('Race')),
            Treatment=clean(row.get('Treatment')),
            Chest_X_Ray=clean(row.get('Chest_X_Ray')),
            Tuberculin_Test=clean(row.get('Tuberculin_Test')),
            Clinical_Form=clean(row.get('Clinical_Form')),
            AIDS_Comorbidity=clean(row.get('AIDS_Comorbidity')),
            Alcoholism_Comorbidity=clean(row.get('Alcoholism_Comorbidity')),
            Diabetes_Comorbidity=clean(row.get('Diabetes_Comorbidity')),
            Mental_Disorder_Comorbidity=clean(row.get('Mental_Disorder_Comorbidity')),
            Other_Comorbidity=clean(row.get('Other_Comorbidity')),
            Drug_Addiction_Comorbidity=clean(row.get('Drug_Addiction_Comorbidity')),
            Smoking_Comorbidity=clean(row.get('Smoking_Comorbidity')),
            HIV=clean(row.get('HIV')),
            Occupational_Disease=clean(row.get('Occupational_Disease')),
            State=clean(row.get('State')),
            Age=clean(row.get('Age'))
        )
        
        # Create Treatment
        t = Treatment.objects.create(
            patient=p,
            Bacilloscopy_Sputum=clean(row.get('Bacilloscopy_Sputum')),
            Bacilloscopy_Sputum_2=clean(row.get('Bacilloscopy_Sputum_2')),
            Bacilloscopy_Other=clean(row.get('Bacilloscopy_Other')),
            Sputum_Culture=clean(row.get('Sputum_Culture')),
            Rifampicin=clean(row.get('Rifampicin')),
            Isoniazid=clean(row.get('Isoniazid')),
            Ethambutol=clean(row.get('Ethambutol')),
            Streptomycin=clean(row.get('Streptomycin')),
            Pyrazinamide=clean(row.get('Pyrazinamide')),
            Ethionamide=clean(row.get('Ethionamide')),
            Other_Drugs=clean(row.get('Other_Drugs')),
            Supervised_Treatment=clean(row.get('Supervised_Treatment')),
            Bacilloscopy_Month_1=clean(row.get('Bacilloscopy_Month_1')),
            Bacilloscopy_Month_2=clean(row.get('Bacilloscopy_Month_2')),
            Bacilloscopy_Month_3=clean(row.get('Bacilloscopy_Month_3')),
            Bacilloscopy_Month_4=clean(row.get('Bacilloscopy_Month_4')),
            Bacilloscopy_Month_5=clean(row.get('Bacilloscopy_Month_5')),
            Bacilloscopy_Month_6=clean(row.get('Bacilloscopy_Month_6')),
            Outcome_Status=clean(row.get('Outcome_Status')),
            Days_In_Treatment=clean(row.get('Days_In_Treatment'))
        )
        
        # Create Dummy Monitoring Visits to trigger Prediction Signal (if >= Month 3)
        from treatments.models import MonitoringVisit
        # Visit 1
        MonitoringVisit.objects.create(
            patient=p, treatment=t, visit_month=1,
            bacilloscopy_result=row.get('Bacilloscopy_Month_1') or 2
        )
        # Visit 2 (Month 3) -> Triggers signal!
        MonitoringVisit.objects.create(
            patient=p, treatment=t, visit_month=3,
            bacilloscopy_result=row.get('Bacilloscopy_Month_3') or 2
        )
        
        created_count += 1
    
    print(f"Success! Imported {created_count} patients and their treatment records.")

if __name__ == "__main__":
    run_import()
