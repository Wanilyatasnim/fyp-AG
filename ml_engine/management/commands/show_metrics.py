from django.core.management.base import BaseCommand
from ml_engine.models import ModelMetric

class Command(BaseCommand):
    help = 'Displays the model performance metrics from the database in the terminal.'

    def handle(self, *args, **options):
        # We can fetch the latest version to show
        latest_metric = ModelMetric.objects.order_by('-created_at').first()
        
        if not latest_metric:
            self.stdout.write(self.style.WARNING("No metrics found in the database. Run 'python manage.py seed_metrics' or train models first."))
            return
            
        version = latest_metric.version
        metrics = ModelMetric.objects.filter(version=version).order_by('-auc_roc')
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Model Performance Metrics (Version: {version}) ==="))
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'Model Name':<20} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10} | {'AUC-ROC':<10}")
        self.stdout.write("-" * 80)
        
        for m in metrics:
            self.stdout.write(f"{m.model_name:<20} | {m.accuracy:<10.4f} | {m.precision:<10.4f} | {m.recall:<10.4f} | {m.f1_score:<10.4f} | {m.auc_roc:<10.4f}")
            
        self.stdout.write("-" * 80)
        self.stdout.write(self.style.SUCCESS("All metrics displayed successfully.\n"))
