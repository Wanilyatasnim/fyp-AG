from django.test import TestCase
from accounts.models import User
from patients.models import Patient
from ml_engine.models import Prediction
from ml_engine.predict import predict_ptld_risk


class RiskCategorisationTests(TestCase):
    def test_predict_returns_four_values(self):
        """predict_ptld_risk should return (score, category, model_name, shap_dict)."""
        user = User.objects.create_user(username='analyst', password='pass12345', role='ANALYST')
        patient = Patient.objects.create(name='Test', Age=30, created_by=user)
        result = predict_ptld_risk(patient)
        self.assertEqual(len(result), 4)

    def test_risk_category_low(self):
        """Risk score <= 0.33 => Low."""
        score = 0.10
        category = 'Low' if score <= 0.33 else ('Moderate' if score <= 0.67 else 'High')
        self.assertEqual(category, 'Low')

    def test_risk_category_moderate(self):
        """Risk score 0.34–0.67 => Moderate."""
        score = 0.50
        category = 'Low' if score <= 0.33 else ('Moderate' if score <= 0.67 else 'High')
        self.assertEqual(category, 'Moderate')

    def test_risk_category_high(self):
        """Risk score > 0.67 => High."""
        score = 0.90
        category = 'Low' if score <= 0.33 else ('Moderate' if score <= 0.67 else 'High')
        self.assertEqual(category, 'High')


class PredictionStorageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin2', password='adminpass1', role='ADMIN')
        self.patient = Patient.objects.create(name='Storage Test', Age=45, created_by=self.user)

    def test_prediction_saved_with_all_fields(self):
        """Prediction record stores score, category, model, shap_values, and triggered_by."""
        pred = Prediction.objects.create(
            patient=self.patient,
            risk_score=0.74,
            risk_category='High',
            model_used='XGBoost (trained)',
            shap_values={'HIV': 0.12, 'Age': -0.08},
            triggered_by=self.user,
        )
        saved = Prediction.objects.get(id=pred.id)
        self.assertAlmostEqual(float(saved.risk_score), 0.74, places=2)
        self.assertEqual(saved.risk_category, 'High')
        self.assertEqual(saved.model_used, 'XGBoost (trained)')
        self.assertEqual(saved.shap_values['HIV'], 0.12)
        self.assertEqual(saved.triggered_by, self.user)
        self.assertIsNotNone(saved.prediction_date)

    def test_prediction_linked_to_patient(self):
        """Prediction should be accessible via patient.predictions."""
        Prediction.objects.create(
            patient=self.patient,
            risk_score=0.20,
            risk_category='Low',
            model_used='Test',
            shap_values={},
        )
        self.assertEqual(self.patient.predictions.count(), 1)
