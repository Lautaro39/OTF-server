import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_otf.settings')
django.setup()

from api.models import AvisoServicio, EventoComunidad

def seed():
    # Clear existing
    print("Clearing existing Avisos and Eventos...")
    AvisoServicio.objects.all().delete()
    EventoComunidad.objects.all().delete()

    # Seed Avisos
    print("Seeding AvisosServicio...")
    AvisoServicio.objects.create(
        titulo='Corte de luz programado',
        descripcion='Trabajos de mantenimiento en la red eléctrica. Afectará a Barrio Norte de 14:00 a 18:00 hs.',
        categoria='Luz',
        fecha_inicio=timezone.now(),
        fecha_fin=timezone.now() + timedelta(hours=4)
    )

    AvisoServicio.objects.create(
        titulo='Reparación de caño maestro',
        descripcion='Corte temporal de suministro de agua potable por reparación sobre Av. Sarmiento al 400.',
        categoria='Agua',
        fecha_inicio=timezone.now() + timedelta(days=1),
        fecha_fin=timezone.now() + timedelta(days=1, hours=6)
    )

    # Seed Eventos
    print("Seeding EventosComunidad...")
    EventoComunidad.objects.create(
        titulo='Feria de Emprendedores',
        descripcion='Feria local con puestos de comida, artesanías y música en vivo de artistas de la zona.',
        ubicacion='Plaza Urquiza',
        fecha_evento=timezone.now() + timedelta(days=2),
    )

    EventoComunidad.objects.create(
        titulo='Campaña de Vacunación Veterinaria',
        descripcion='Campaña gratuita de vacunación antirrábica y desparasitación para perros y gatos.',
        ubicacion='CAPS San Martín',
        fecha_evento=timezone.now() + timedelta(days=3),
    )

    print("Database seeded successfully with community notices and events!")

if __name__ == '__main__':
    seed()
