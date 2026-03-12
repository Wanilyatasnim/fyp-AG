from django.apps import AppConfig

class MlEngineConfig(AppConfig):
    name = 'ml_engine'

    def ready(self):
        import ml_engine.signals
