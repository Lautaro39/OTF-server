from django.core.management.base import BaseCommand

from api.models import Categoria, Estado


class Command(BaseCommand):
    help = 'Seed the database with initial Categoria and Estado data'

    def handle(self, *args, **options):
        categorias = [
            ('Alumbrado', 'Problemas con iluminacion publica'),
            ('Limpieza', 'Problemas de residuos, limpieza urbana'),
            ('Vandalismo', 'Actos de vandalismo, grafitis, danos'),
            ('Bache', 'Baches y problemas en la via publica'),
        ]
        for nombre, descripcion in categorias:
            obj, created = Categoria.objects.get_or_create(
                nombre=nombre, defaults={'descripcion': descripcion}
            )
            self.stdout.write(
                self.style.SUCCESS(f'Categoria "{nombre}": {"creada" if created else "ya existe"}')
            )

        estados = [
            ('Pendiente', 'Denuncia recibida, pendiente de revision'),
            ('En revision', 'Un administrador esta evaluando la denuncia'),
            ('Resuelta', 'El problema fue solucionado'),
            ('Rechazada', 'La denuncia fue rechazada por un administrador'),
        ]
        for nombre, descripcion in estados:
            obj, created = Estado.objects.get_or_create(
                nombre_estado=nombre, defaults={'descripcion': descripcion}
            )
            self.stdout.write(
                self.style.SUCCESS(f'Estado "{nombre}": {"creado" if created else "ya existe"}')
            )

        self.stdout.write(self.style.SUCCESS('\nSeed completado.'))
