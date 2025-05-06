from django.apps import AppConfig


class CorrespondenciaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'correspondencia'
    def ready(self):
            import correspondencia.signals  # <<<< Esto importa y activa las señales