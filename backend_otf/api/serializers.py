from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import (
    Administrador,
    Archivo,
    AuditCambio,
    CarpetaArchivo,
    Categoria,
    Denuncia,
    DenunciaTag,
    Estado,
    EstadoDenuncia,
    InfoUsuario,
    LogAcceso,
    Notificacion,
    PreferenciaUsuario,
    Rol,
    TagDenuncia,
    TelefonoUsuario,
    Usuario,
    UsuarioRol,
    Voto,
)

# ---------------------------------------------------------------------------
# Auth — serializers para el frontend Flutter de One-Trough-Five
# ---------------------------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(self.context.get('request'), email=email, password=password)
        if user is None:
            raise serializers.ValidationError('Credenciales inválidas.')
        if not user.is_active:
            raise serializers.ValidationError('Cuenta desactivada.')
        attrs['user'] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, max_length=150)
    lastname = serializers.CharField(write_only=True, max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, max_length=50, required=False, allow_blank=True)
    dni = serializers.CharField(write_only=True, max_length=50, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = Usuario
        fields = ['email', 'password', 'name', 'lastname', 'phone', 'dni']

    def create(self, validated_data):
        name = validated_data.pop('name')
        lastname = validated_data.pop('lastname', '')
        phone = validated_data.pop('phone', '')
        dni = validated_data.pop('dni', '')
        password = validated_data.pop('password')
        email = validated_data.get('email')

        username = email.split('@')[0]
        user = Usuario.objects.create_user(
            username=username,
            email=email,
            first_name=name,
            last_name=lastname,
            password=password,
        )
        InfoUsuario.objects.create(
            id_usuario=user,
            dni=dni or None,
            telefono=phone or None,
        )
        return user


class UserResponseSerializer(serializers.Serializer):
    """Formato de usuario que espera el frontend Flutter."""
    id = serializers.IntegerField(source='id_usuario')
    name = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    email = serializers.EmailField()
    phone = serializers.SerializerMethodField()
    dni = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_phone(self, obj):
        try:
            return obj.infousuario.telefono
        except InfoUsuario.DoesNotExist:
            return None

    def get_dni(self, obj):
        try:
            return obj.infousuario.dni
        except InfoUsuario.DoesNotExist:
            return None

    def get_image(self, obj):
        return None


class ProfilePutSerializer(serializers.Serializer):
    """Actualización de perfil vía multipart (PUT /auth/upload/<id>/)."""
    name = serializers.CharField(max_length=150, required=False)
    lastname = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    image = serializers.FileField(required=False)

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        lastname = validated_data.get('lastname')
        phone = validated_data.get('phone')
        # image se ignora (no hay campo de imagen todavía)

        if name is not None:
            instance.first_name = name
        if lastname is not None:
            instance.last_name = lastname
        instance.save()

        if phone is not None:
            InfoUsuario.objects.update_or_create(
                id_usuario=instance,
                defaults={'telefono': phone},
            )

        return instance

# ---------------------------------------------------------------------------
# Usuarios, roles y administración
# ---------------------------------------------------------------------------


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id_usuario',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'date_joined',
            'is_active',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'date_joined': {'read_only': True},
        }


class InfoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfoUsuario
        fields = [
            'id_usuario',
            'domicilio',
            'dni',
            'telefono',
        ]


class AdministradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrador
        fields = [
            'id_usuario',
            'legajo',
            'fecha_ingreso',
            'rol_admin',
        ]


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id_rol', 'nombre_rol']


class UsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioRol
        fields = ['id', 'id_usuario', 'id_rol']


# ---------------------------------------------------------------------------
# Denuncias, estados y categorías
# ---------------------------------------------------------------------------


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id_categoria', 'nombre', 'descripcion']


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['id_estado', 'nombre_estado', 'descripcion']


class DenunciaListSerializer(serializers.ModelSerializer):
    """Denuncia en listados: incluye labels de relaciones en lugar de solo IDs."""

    nombre_usuario = serializers.CharField(source='id_usuario.username', read_only=True)
    categoria = serializers.CharField(source='id_categoria.nombre', read_only=True)
    estado = serializers.CharField(source='estado_actual.nombre_estado', read_only=True)

    class Meta:
        model = Denuncia
        fields = [
            'id_denuncia',
            'id_usuario',
            'nombre_usuario',
            'id_categoria',
            'categoria',
            'titulo',
            'descripcion',
            'fecha_creacion',
            'estado_actual',
            'estado',
        ]
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }


class DenunciaDetailSerializer(serializers.ModelSerializer):
    """Denuncia en detalle: incluye objetos anidados completos."""

    id_usuario = UsuarioSerializer(read_only=True)
    id_categoria = CategoriaSerializer(read_only=True)
    estado_actual = EstadoSerializer(read_only=True)

    class Meta:
        model = Denuncia
        fields = [
            'id_denuncia',
            'id_usuario',
            'id_categoria',
            'titulo',
            'descripcion',
            'fecha_creacion',
            'estado_actual',
        ]
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }


class DenunciaWriteSerializer(serializers.ModelSerializer):
    """Denuncia para creación y actualización: solo IDs en relaciones."""

    class Meta:
        model = Denuncia
        fields = [
            'id_denuncia',
            'id_usuario',
            'id_categoria',
            'titulo',
            'descripcion',
            'estado_actual',
        ]
        extra_kwargs = {
            'id_denuncia': {'read_only': True},
        }


class EstadoDenunciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoDenuncia
        fields = [
            'id_estado_denuncia',
            'id_denuncia',
            'id_estado',
            'id_admin',
            'comentario_admin',
            'fecha_cambio',
        ]
        extra_kwargs = {
            'fecha_cambio': {'read_only': True},
        }


# ---------------------------------------------------------------------------
# Votos
# ---------------------------------------------------------------------------


class VotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voto
        fields = [
            'id_voto',
            'id_usuario',
            'id_denuncia',
            'descripcion',
            'fecha',
        ]
        extra_kwargs = {
            'fecha': {'read_only': True},
        }


# ---------------------------------------------------------------------------
# Archivos y carpetas
# ---------------------------------------------------------------------------


class CarpetaArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarpetaArchivo
        fields = [
            'id_carpeta',
            'id_denuncia',
            'nombre_carpeta',
            'fecha_creacion',
        ]
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }


class ArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archivo
        fields = [
            'id_archivo',
            'id_carpeta',
            'nombre_archivo',
            'ruta',
            'tipo_mime',
            'tamano_bytes',
            'fecha_subida',
        ]
        extra_kwargs = {
            'fecha_subida': {'read_only': True},
        }


# ---------------------------------------------------------------------------
# Logs, auditoría y notificaciones
# ---------------------------------------------------------------------------


class LogAccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAcceso
        fields = [
            'id_log',
            'id_usuario',
            'fecha_hora',
            'ip',
            'user_agent',
            'resultado',
        ]
        extra_kwargs = {
            'fecha_hora': {'read_only': True},
        }


class AuditCambioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditCambio
        fields = [
            'id_audit',
            'tabla',
            'id_registro',
            'id_usuario',
            'operacion',
            'fecha_hora',
            'detalle_antes',
            'detalle_despues',
        ]
        extra_kwargs = {
            'fecha_hora': {'read_only': True},
        }


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = [
            'id_notificacion',
            'id_usuario',
            'tipo',
            'contenido',
            'leida',
            'fecha_envio',
        ]
        extra_kwargs = {
            'fecha_envio': {'read_only': True},
        }


# ---------------------------------------------------------------------------
# Tablas auxiliares
# ---------------------------------------------------------------------------


class TelefonoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelefonoUsuario
        fields = [
            'id_telefono',
            'id_usuario',
            'telefono',
            'tipo',
            'principal',
        ]


class TagDenunciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagDenuncia
        fields = ['id_tag', 'nombre_tag']


class DenunciaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenunciaTag
        fields = ['id', 'id_denuncia', 'id_tag']


class PreferenciaUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenciaUsuario
        fields = [
            'id_usuario',
            'recibir_emails',
            'idioma',
            'zona_horaria',
        ]
