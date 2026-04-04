from django.core.management.base import BaseCommand
from ml_engine.models import ModelMetric

class Command(BaseCommand):
    help = 'Seeds the initial model performance metrics'

    def handle(self, *args, **options):
        # Sample realistic metrics for the XGBoost model
        metrics = {
            'version': '1.0.4 (Current)',
            'model_name': 'XGBoost Classifier',
            'accuracy': 0.912,
            'precision': 0.885,
            'recall': 0.941,
            'f1_score': 0.912,
            'auc_roc': 0.934,
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
                'Treatment': 0.017
            }
        }

        obj, created = ModelMetric.objects.update_or_create(
            version=metrics['version'],
            defaults=metrics
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully seeded metrics.'))
        else:
            self.stdout.write(self.style.SUCCESS('Metrics already exists, updated content.'))
