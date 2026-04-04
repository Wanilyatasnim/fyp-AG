def get_clinical_recommendations(risk_category):
    """
    Returns a list of clinical actions based on the PTLD risk category.
    """
    recommendations = {
        'High': [
            "Schedule pulmonary function test (spirometry) within 4 weeks",
            "Refer to pulmonologist for specialist evaluation",
            "Chest X-ray or CT scan follow-up",
            "Screen for respiratory symptoms (dyspnea, chronic cough)",
            "Monitor for bronchiectasis and fibrosis indicators",
            "Increase follow-up frequency to every 2 weeks"
        ],
        'Moderate': [
            "Schedule pulmonary function test within 8 weeks",
            "Monitor respiratory symptoms at every visit",
            "Chest X-ray at treatment completion",
            "Educate patient on PTLD warning signs",
            "Follow up at 6 months post-treatment"
        ],
        'Low': [
            "Standard end-of-treatment review",
            "Chest X-ray at 6 months post-treatment",
            "Advise patient to return if respiratory symptoms develop"
        ]
    }
    return recommendations.get(risk_category, [])
