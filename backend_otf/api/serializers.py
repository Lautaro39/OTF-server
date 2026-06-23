from rest_framework import serializers

from .models import (
    Administrador,
    Archivo,
    AsistenciaEvento,
    AuditCambio,
    AvisoServicio,
    CarpetaArchivo,
    Categoria,
    Denuncia,
    DenunciaTag,
    Estado,
    EstadoDenuncia,
    EventoComunidad,
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
    Equipo,
    MiembroEquipo,
)


# =========================================================================
# Auth serializers (Flutter contract)
# =========================================================================


class UserResponseSerializer(serializers.ModelSerializer):
    """Flutter UserModel contract: flat shape, no roles, no email."""
    name = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    phone = serializers.SerializerMethodField()
    dni = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    legajo = serializers.SerializerMethodField()
    area = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'name', 'lastname', 'phone', 'dni', 'image', 'legajo', 'area']

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
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None

    def get_legajo(self, obj):
        try:
            return obj.administrador.legajo
        except Exception:
            return None

    def get_area(self, obj):
        try:
            return obj.administrador.rol_admin
        except Exception:
            return None


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, source='first_name')
    lastname = serializers.CharField(max_length=150, source='last_name')
    username = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=50, allow_blank=True, required=False)
    password = serializers.CharField(min_length=4, style={'input_type': 'password'})

    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con ese DNI.')
        return value

    def create(self, validated_data):
        from django.db import transaction

        with transaction.atomic():
            user = Usuario.objects.create_user(
                username=validated_data['username'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
            )
            InfoUsuario.objects.create(
                id_usuario=user,
                dni=validated_data['username'],
                telefono=validated_data.get('phone', ''),
            )
        return user


class ProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, source='first_name', required=False)
    lastname = serializers.CharField(max_length=150, source='last_name', required=False)
    phone = serializers.CharField(max_length=50, allow_blank=True, required=False)
    image = serializers.ImageField(required=False)

    def update(self, user, validated_data):
        if 'first_name' in validated_data:
            user.first_name = validated_data['first_name']
        if 'last_name' in validated_data:
            user.last_name = validated_data['last_name']
        if 'image' in validated_data:
            user.imagen = validated_data['image']
        user.save()

        info, _ = InfoUsuario.objects.get_or_create(id_usuario=user)
        if 'phone' in validated_data:
            info.telefono = validated_data['phone']
            info.save()

        return user


# =========================================================================
# Usuarios, roles y administracion
# =========================================================================


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'date_joined',
            'imagen',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'date_joined': {'read_only': True},
        }


class InfoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfoUsuario
        fields = ['id_usuario', 'domicilio', 'dni', 'telefono']


class AdministradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrador
        fields = ['id_usuario', 'legajo', 'fecha_ingreso', 'rol_admin']


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id_rol', 'nombre_rol']


class UsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioRol
        fields = ['id', 'id_usuario', 'id_rol']


# =========================================================================
# Denuncias, estados y categorias
# =========================================================================


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id_categoria', 'nombre', 'descripcion']


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['id_estado', 'nombre_estado', 'descripcion']


class DenunciaListSerializer(serializers.ModelSerializer):
    """Denuncia en listados: labels legibles en lugar de solo IDs."""

    nombre_usuario = serializers.CharField(source='id_usuario.first_name', read_only=True)
    categoria = serializers.CharField(source='id_categoria.nombre', read_only=True)
    estado = serializers.CharField(source='estado_actual.nombre_estado', read_only=True)
    imagen = serializers.SerializerMethodField()

    class Meta:
        model = Denuncia
        fields = [
            'id_denuncia',
            'id_usuario',
            'nombre_usuario',
            'id_categoria',
            'categoria',
            'descripcion',
            'latitud',
            'longitud',
            'direccion',
            'imagen',
            'fecha_creacion',
            'estado_actual',
            'estado',
        ]
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }

    def get_imagen(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class DenunciaDetailSerializer(serializers.ModelSerializer):
    """Denuncia en detalle: objetos anidados completos."""

    id_usuario = UserResponseSerializer(read_only=True)
    id_categoria = CategoriaSerializer(read_only=True)
    estado_actual = EstadoSerializer(read_only=True)
    imagen = serializers.SerializerMethodField()

    class Meta:
        model = Denuncia
        fields = [
            'id_denuncia',
            'id_usuario',
            'id_categoria',
            'descripcion',
            'latitud',
            'longitud',
            'direccion',
            'imagen',
            'fecha_creacion',
            'estado_actual',
        ]
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }

    def get_imagen(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None


class DenunciaWriteSerializer(serializers.ModelSerializer):
    """Denuncia para creacion y actualizacion: solo IDs en relaciones."""
    latitud = serializers.DecimalField(max_digits=20, decimal_places=15, required=False, allow_null=True)
    longitud = serializers.DecimalField(max_digits=20, decimal_places=15, required=False, allow_null=True)

    class Meta:
        model = Denuncia
        fields = [
            'id_denuncia',
            'id_usuario',
            'id_categoria',
            'descripcion',
            'latitud',
            'longitud',
            'direccion',
            'imagen',
            'estado_actual',
        ]
        extra_kwargs = {
            'id_denuncia': {'read_only': True},
            'id_usuario': {'read_only': True},
            'estado_actual': {'read_only': True},
        }

    def validate(self, attrs):
        if 'latitud' in attrs and attrs['latitud'] is not None:
            attrs['latitud'] = round(attrs['latitud'], 6)
        if 'longitud' in attrs and attrs['longitud'] is not None:
            attrs['longitud'] = round(attrs['longitud'], 6)
        return attrs


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


# =========================================================================
# Votos
# =========================================================================


class VotoSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(source='id_usuario.first_name', read_only=True)

    class Meta:
        model = Voto
        fields = [
            'id_voto',
            'id_usuario',
            'nombre_usuario',
            'id_denuncia',
            'descripcion',
            'fecha',
        ]
        extra_kwargs = {
            'id_usuario': {'read_only': True},
            'fecha': {'read_only': True},
        }


# =========================================================================
# Archivos y carpetas
# =========================================================================


class CarpetaArchivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarpetaArchivo
        fields = ['id_carpeta', 'id_denuncia', 'nombre_carpeta', 'fecha_creacion']
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }


class ArchivoSerializer(serializers.ModelSerializer):
    id_denuncia = serializers.IntegerField(write_only=True)

    class Meta:
        model = Archivo
        fields = [
            'id_archivo',
            'id_carpeta',
            'id_denuncia',
            'nombre_archivo',
            'ruta',
            'tipo_mime',
            'tamano_bytes',
            'archivo',
            'fecha_subida',
        ]
        extra_kwargs = {
            'id_carpeta': {'read_only': True},
            'nombre_archivo': {'read_only': True},
            'ruta': {'read_only': True},
            'tipo_mime': {'read_only': True},
            'tamano_bytes': {'read_only': True},
            'fecha_subida': {'read_only': True},
        }


# =========================================================================
# Logs, auditoria y notificaciones
# =========================================================================


class LogAccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAcceso
        fields = ['id_log', 'id_usuario', 'fecha_hora', 'ip', 'user_agent', 'resultado']
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
        fields = ['id_notificacion', 'id_usuario', 'tipo', 'contenido', 'leida', 'fecha_envio']
        extra_kwargs = {
            'fecha_envio': {'read_only': True},
        }


# =========================================================================
# Tablas auxiliares
# =========================================================================


class TelefonoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelefonoUsuario
        fields = ['id_telefono', 'id_usuario', 'telefono', 'tipo', 'principal']


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
        fields = ['id_usuario', 'recibir_emails', 'idioma', 'zona_horaria']


class AvisoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvisoServicio
        fields = '__all__'


class EventoComunidadSerializer(serializers.ModelSerializer):
    asistentes_count = serializers.IntegerField(read_only=True)
    is_attending = serializers.SerializerMethodField()
    imagen = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = EventoComunidad
        fields = [
            'id_evento',
            'titulo',
            'descripcion',
            'ubicacion',
            'fecha_evento',
            'imagen',
            'asistentes_count',
            'is_attending',
            'fecha_creacion',
        ]
        extra_kwargs = {
            'fecha_creacion': {'read_only': True},
        }

    def get_is_attending(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.asistentes.filter(id=request.user.id).exists()
        return False


class AdminDenunciaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='id_denuncia', read_only=True)
    categoria = serializers.CharField(source='id_categoria.nombre', allow_null=True, required=False)
    foto_url = serializers.SerializerMethodField()
    estado = serializers.CharField(source='estado_actual.nombre_estado', allow_null=True, required=False)
    master_case_id = serializers.PrimaryKeyRelatedField(source='master_case', read_only=True)
    creador_dni = serializers.SerializerMethodField()
    nombre_equipo = serializers.CharField(source='equipo_asignado.nombre', read_only=True, allow_null=True)

    class Meta:
        model = Denuncia
        fields = [
            'id',
            'categoria',
            'descripcion',
            'foto_url',
            'direccion',
            'latitud',
            'longitud',
            'fecha_creacion',
            'estado',
            'equipo_asignado',
            'nombre_equipo',
            'master_case_id',
            'creador_dni',
        ]

    def get_foto_url(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None

    def get_creador_dni(self, obj):
        try:
            return obj.id_usuario.infousuario.dni
        except Exception:
            return ''


class MiembroEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiembroEquipo
        fields = ['id_miembro', 'dni', 'cargo']


class EquipoSerializer(serializers.ModelSerializer):
    miembros = MiembroEquipoSerializer(many=True, required=False)
    categoria_nombre = serializers.CharField(source='id_categoria.nombre', read_only=True)

    class Meta:
        model = Equipo
        fields = ['id_equipo', 'nombre', 'id_categoria', 'categoria_nombre', 'miembros', 'fecha_creacion']
        extra_kwargs = {
            'nombre': {'read_only': True},
        }

    def create(self, validated_data):
        miembros_data = validated_data.pop('miembros', [])
        from django.db import transaction
        with transaction.atomic():
            equipo = Equipo.objects.create(**validated_data)
            for miembro_data in miembros_data:
                MiembroEquipo.objects.create(id_equipo=equipo, **miembro_data)
        return equipo
