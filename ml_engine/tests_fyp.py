import os
from django.test import TestCase
from accounts.models import User
from patients.models import Patient
from ml_engine.predict import predict_ptld_risk
from ml_engine.models import ModelMetric

class MLModelTests(TestCase):
    def setUp(self):
        # Create a sample patient with sufficient data for a real prediction
        self.clinician = User.objects.create_user(username='ml_clinician', password='p', role='CLINICIAN')
        self.patient = Patient.objects.create(
            name='ML Test Patient',
            Age=68, # High age risk
            Sex=1,
            Race=1,
            HIV=1, # Positive
            Clinical_Form=1,
            Chest_X_Ray=1, # Cavitary (High Risk)
            assigned_clinician=self.clinician
        )

    def test_T48_model_loads_without_error(self):
        """T48: Verify that model files (.pkl) are discoverable and loadable."""
        from ml_engine.predict import _load_model
        # We check for at least ONE model (XGBoost or Random Forest)
        xgb = _load_model('xgboost')
        rf = _load_model('random_forest')
        self.assertTrue(xgb is not None or rf is not None, "At least one trained model should be found in ml_engine/models/")

    def test_T23_T49_prediction_output_range(self):
        """T23 & T49: Verify prediction returns a valid score between 0.0 and 1.0."""
        score, category, model_name, shap_values = predict_ptld_risk(self.patient)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn(category, ['Low', 'Moderate', 'High'])
        print(f"DEBUG: T23 Score={score}, Category={category}, Model={model_name}")

    def test_T50_shap_values_generation(self):
        """T50: Verify SHAP values are generated and contain top features."""
        score, category, model_name, shap_values = predict_ptld_risk(self.patient)
        # Even with fallback, we expect some feature analysis
        self.assertGreater(len(shap_values), 0)
        self.assertTrue(any(v != 0.0 for v in shap_values.values()), "SHAP values should not be all zero if model is active.")

    def test_T51_model_metric_exists(self):
        """T51: Verify ModelMetric record can be queried for performance auditing."""
        # Create a dummy metric record as per previous instructions
        ModelMetric.objects.create(
            model_name="XGBoost_Production",
            auroc=0.89,
            accuracy=0.85,
            f1_score=0.82
        )
        metric = ModelMetric.objects.latest('created_at')
        self.assertEqual(metric.auroc, 0.89)
        self.assertEqual(metric.model_name, "XGBoost_Production")
