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

        # 3. Crear usuario administrador de prueba (12345678 / admin123)
        from api.models import Usuario, InfoUsuario, Administrador
        from django.contrib.auth.hashers import make_password

        admin_user, created = Usuario.objects.get_or_create(username='12345678')
        if created:
            admin_user.first_name = 'Pedro'
            admin_user.last_name = 'Administrador'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.password = make_password('admin123')
            admin_user.save()

            InfoUsuario.objects.get_or_create(
                id_usuario=admin_user,
                defaults={'dni': '12345678', 'telefono': '3871234567'}
            )

            Administrador.objects.get_or_create(
                id_usuario=admin_user,
                defaults={'legajo': 'L-4091', 'rol_admin': 'Servicios Públicos'}
            )
            self.stdout.write(self.style.SUCCESS('Admin "12345678": creado con contraseña "admin123"'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin "12345678": ya existe'))

        self.stdout.write(self.style.SUCCESS('\nSeed completado.'))
