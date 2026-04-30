from django.core.management.base import BaseCommand
from ml_engine.models import ModelMetric


class Command(BaseCommand):
    help = 'Seeds realistic per-model performance metrics for all 3 models (LR, RF, XGBoost)'

    def handle(self, *args, **options):
        VERSION = '1.0.4 (Current)'

        # Delete existing entries for this version to avoid duplicates
        ModelMetric.objects.filter(version=VERSION).delete()

        models_data = [
            {
                'model_name': 'XGBoost',
                'accuracy': 0.912,
                'precision': 0.885,
                'recall': 0.941,
                'f1_score': 0.912,
                'auc_roc': 0.967,
                'global_importance': {
                    'Smoking_Comorbidity': 0.245,
                    'Diabetes_Comorbidity': 0.182,
                    'Age': 0.154,
                    'Bacilloscopy_Month_2': 0.121,
                    'HIV': 0.098,
                    'Chest_X_Ray': 0.085,
                    'Sex': 0.042,
                    'Rifampicin': 0.031,
                    'Alcoholism_Comorbidity': 0.025,
                    'Treatment': 0.017,
                },
            },
            {
                'model_name': 'RandomForest',
                'accuracy': 0.901,
                'precision': 0.871,
                'recall': 0.928,
                'f1_score': 0.899,
                'auc_roc': 0.951,
                'global_importance': {},
            },
            {
                'model_name': 'LogisticRegression',
                'accuracy': 0.867,
                'precision': 0.833,
                'recall': 0.895,
                'f1_score': 0.863,
                'auc_roc': 0.921,
                'global_importance': {},
            },
        ]

        for m in models_data:
            ModelMetric.objects.create(version=VERSION, **m)
            self.stdout.write(self.style.SUCCESS(f'Seeded metrics for {m["model_name"]}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nAll 3 model metrics seeded successfully for version {VERSION}.'
        ))
