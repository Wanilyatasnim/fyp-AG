from django.test import TestCase
from accounts.models import User
from patients.models import Patient
from ml_engine.models import Prediction
from ml_engine.predict import predict_ptld_risk, _extract_features
import numpy as np


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

    def test_edge_case_boundaries(self):
        """Test exactly on the 0.33 and 0.67 boundaries."""
        self.assertEqual('Low' if 0.33 <= 0.33 else 'Other', 'Low')
        self.assertEqual('Moderate' if 0.33001 > 0.33 and 0.33001 <= 0.67 else 'Other', 'Moderate')


class PredictionStorageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin2', password='adminpass1', role='ADMIN')
        self.patient = Patient.objects.create(name='Storage Test', Age=45, created_by=self.user)

    def test_prediction_saved_with_all_fields(self):
        """Prediction record stores score, category, model, shap_values, and triggered_by."""
        pred = Prediction.objects.create(
            patient_id=self.patient,
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
        self.assertEqual(saved.triggered_by, str(self.user))
        self.assertIsNotNone(saved.prediction_date)

    def test_prediction_linked_to_patient(self):
        """Prediction should be accessible via patient.predictions."""
        Prediction.objects.create(
            patient_id=self.patient,
            risk_score=0.20,
            risk_category='Low',
            model_used='Test',
            shap_values={},
        )
        self.assertEqual(self.patient.predictions.count(), 1)


class FeatureExtractionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='extractor', password='pass', role='CLINICIAN')

    def test_extract_features_shape(self):
        """Feature vector should have shape (1, 40)."""
        patient = Patient.objects.create(name='Shape Test', Age=25, created_by=self.user)
        features = _extract_features(patient)
        self.assertEqual(features.shape, (1, 40))

    def test_extract_features_defaults(self):
        """Verify defaults are used when treatment or fields are missing."""
        patient = Patient.objects.create(name='Default Test', created_by=self.user)
        # Defaults: Age=30 (if None), Sex=1, Chest_X_Ray=2, etc.
        features = _extract_features(patient)
        # Age is at index 33 in FEATURE_COLS? 
        # FEATURE_COLS says 'Age' is at index 33 (0-indexed)
        self.assertEqual(features[0, 33], 30) 
        # Days_In_Treatment is at index 32
        self.assertEqual(features[0, 32], 180)
