import os
from django.apps import AppConfig
from django.conf import settings
import firebase_admin
from firebase_admin import credentials

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        # Evita inicializaciones duplicadas cuando Django se recarga automáticamente en desarrollo
        if not firebase_admin._apps:
            cred_path = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("[INFO] Firebase Admin SDK inicializado correctamente.")
            else:
                print(f"[WARNING] No se encontró el archivo de credenciales de Firebase en: {cred_path}")