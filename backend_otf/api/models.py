from django.db import models

# ---------------------------------------------------------------------------
# Usuarios, roles y administración
# ---------------------------------------------------------------------------

class Usuario(models.Model):
    """Usuario principal del sistema."""
    id_usuario = models.BigAutoField(primary_key=True, db_column='IdUsuario')
    nombre_usuario = models.CharField(max_length=100, unique=True, db_column='NombreUsuario')
    contra_encriptada = models.CharField(max_length=255, db_column='ContraEncriptada')
    fecha_alta = models.DateTimeField(auto_now_add=True, db_column='FechaAlta')
    activo = models.BooleanField(default=True, db_column='Activo')

    class Meta:
        db_table = 'Usuarios'
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['nombre_usuario']

    def __str__(self):
        return self.nombre_usuario


class InfoUsuario(models.Model):
    """Información extendida del usuario (1:1 con Usuario)."""
    id_usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, primary_key=True, db_column='IdUsuario'
    )
    email = models.EmailField(max_length=255, unique=True, db_column='Email')
    domicilio = models.CharField(max_length=255, blank=True, null=True, db_column='Domicilio')
    dni = models.CharField(max_length=50, unique=True, blank=True, null=True, db_column='DNI')
    # Teléfono de contacto principal. Para múltiples teléfonos por usuario
    # existe la tabla TelefonosUsuario (ver modelo TelefonoUsuario).
    telefono = models.CharField(max_length=50, blank=True, null=True, db_column='Telefono')

    class Meta:
        db_table = 'InfoUsuarios'
        verbose_name = 'info de usuario'
        verbose_name_plural = 'info de usuarios'

    def __str__(self):
        return f'Info de {self.id_usuario}'


class Administrador(models.Model):
    """Usuario con privilegios de administración."""
    id_usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, primary_key=True, db_column='IdUsuario'
    )
    legajo = models.CharField(max_length=50, unique=True, blank=True, null=True, db_column='Legajo')
    fecha_ingreso = models.DateField(blank=True, null=True, db_column='FechaIngreso')
    rol_admin = models.CharField(max_length=50, blank=True, null=True, db_column='RolAdmin')

    class Meta:
        db_table = 'Administradores'
        verbose_name = 'administrador'
        verbose_name_plural = 'administradores'

    def __str__(self):
        return f'Admin {self.id_usuario}'


class Rol(models.Model):
    """Roles asignables a usuarios (ej. editor, revisor, superadmin)."""
    id_rol = models.AutoField(primary_key=True, db_column='IdRol')
    nombre_rol = models.CharField(max_length=100, unique=True, db_column='NombreRol')

    class Meta:
        db_table = 'Roles'
        verbose_name = 'rol'
        verbose_name_plural = 'roles'

    def __str__(self):
        return self.nombre_rol


class UsuarioRol(models.Model):
    """
    Relación muchos-a-muchos entre Usuario y Rol.

    Django no soporta claves primarias compuestas nativamente, por lo que se
    usa un UniqueConstraint en (IdUsuario, IdRol) en lugar de una PK compuesta.
    """
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario')
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='IdRol')

    class Meta:
        db_table = 'UsuariosRoles'
        verbose_name = 'usuario-rol'
        verbose_name_plural = 'usuarios-roles'
        constraints = [
            models.UniqueConstraint(fields=['id_usuario', 'id_rol'], name='uq_ur_usuario_rol'),
        ]

    def __str__(self):
        return f'{self.id_usuario} -> {self.id_rol}'


# ---------------------------------------------------------------------------
# Denuncias, estados y categorías
# ---------------------------------------------------------------------------

class Categoria(models.Model):
    """Categoría a la que pertenece una denuncia."""
    id_categoria = models.AutoField(primary_key=True, db_column='IdCategoria')
    nombre = models.CharField(max_length=150, unique=True, db_column='Nombre')
    descripcion = models.TextField(blank=True, null=True, db_column='Descripcion')

    class Meta:
        db_table = 'Categorias'
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Estado(models.Model):
    """Catálogo de estados por los que puede pasar una denuncia."""
    id_estado = models.AutoField(primary_key=True, db_column='IdEstado')
    nombre_estado = models.CharField(max_length=100, unique=True, db_column='NombreEstado')
    descripcion = models.TextField(blank=True, null=True, db_column='Descripcion')

    class Meta:
        db_table = 'Estados'
        verbose_name = 'estado'
        verbose_name_plural = 'estados'
        ordering = ['nombre_estado']

    def __str__(self):
        return self.nombre_estado


class Denuncia(models.Model):
    """
    Denuncia presentada por un usuario.

    Se utiliza SET_NULL en las FK a Categoria y Estado (en lugar de NO ACTION)
    para evitar errores al eliminar registros referenciados sin perder la
    denuncia. En esos casos la columna queda en NULL.
    """
    id_denuncia = models.BigAutoField(primary_key=True, db_column='IdDenuncia')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario')
    id_categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, blank=True, null=True, db_column='IdCategoria'
    )
    titulo = models.CharField(max_length=255, blank=True, null=True, db_column='Titulo')
    descripcion = models.TextField(blank=True, null=True, db_column='Descripcion')
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FechaCreacion')
    # Estado en el que se encuentra la denuncia actualmente.
    estado_actual = models.ForeignKey(
        Estado,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_column='EstadoActualId',
        related_name='denuncias_estado_actual',
    )

    class Meta:
        db_table = 'Denuncias'
        verbose_name = 'denuncia'
        verbose_name_plural = 'denuncias'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo or f'Denuncia #{self.id_denuncia}'


class EstadoDenuncia(models.Model):
    """
    Historial de cambios de estado de una denuncia.

    Cada fila registra cuándo un administrador cambió el estado de una denuncia.
    """
    id_estado_denuncia = models.BigAutoField(primary_key=True, db_column='IdEstadoDenuncia')
    id_denuncia = models.ForeignKey(Denuncia, on_delete=models.CASCADE, db_column='IdDenuncia')
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='IdEstado')
    # Si el admin es eliminado, el historial conserva la referencia en NULL.
    id_admin = models.ForeignKey(
        Administrador, on_delete=models.SET_NULL, blank=True, null=True, db_column='IdAdmin'
    )
    comentario_admin = models.TextField(blank=True, null=True, db_column='ComentarioAdmin')
    fecha_cambio = models.DateTimeField(auto_now_add=True, db_column='FechaCambio')

    class Meta:
        db_table = 'EstadoDenuncias'
        verbose_name = 'historial de estado'
        verbose_name_plural = 'historiales de estado'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f'Denuncia #{self.id_denuncia_id} → {self.id_estado_id}'


# ---------------------------------------------------------------------------
# Votos
# ---------------------------------------------------------------------------

class Voto(models.Model):
    """Voto emitido por un usuario sobre una denuncia. Un mismo usuario solo
    puede votar una vez por denuncia (UniqueConstraint)."""
    id_voto = models.BigAutoField(primary_key=True, db_column='IdVoto')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario')
    id_denuncia = models.ForeignKey(Denuncia, on_delete=models.CASCADE, db_column='IdDenuncia')
    descripcion = models.TextField(blank=True, null=True, db_column='Descripcion')
    fecha = models.DateTimeField(auto_now_add=True, db_column='Fecha')

    class Meta:
        db_table = 'Votos'
        verbose_name = 'voto'
        verbose_name_plural = 'votos'
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(fields=['id_usuario', 'id_denuncia'], name='uq_voto_usuario_denuncia'),
        ]

    def __str__(self):
        return f'Voto de {self.id_usuario_id} en denuncia #{self.id_denuncia_id}'


# ---------------------------------------------------------------------------
# Archivos y carpetas
# ---------------------------------------------------------------------------

class CarpetaArchivo(models.Model):
    """Carpeta contenedora de archivos adjuntos a una denuncia."""
    id_carpeta = models.BigAutoField(primary_key=True, db_column='IdCarpeta')
    id_denuncia = models.ForeignKey(Denuncia, on_delete=models.CASCADE, db_column='IdDenuncia')
    nombre_carpeta = models.CharField(max_length=255, blank=True, null=True, db_column='NombreCarpeta')
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='FechaCreacion')

    class Meta:
        db_table = 'CarpetaArchivos'
        verbose_name = 'carpeta de archivos'
        verbose_name_plural = 'carpetas de archivos'

    def __str__(self):
        return self.nombre_carpeta or f'Carpeta #{self.id_carpeta}'


class Archivo(models.Model):
    """Archivo almacenado dentro de una carpeta de denuncia."""
    id_archivo = models.BigAutoField(primary_key=True, db_column='IdArchivo')
    id_carpeta = models.ForeignKey(CarpetaArchivo, on_delete=models.CASCADE, db_column='IdCarpeta')
    nombre_archivo = models.CharField(max_length=255, blank=True, null=True, db_column='NombreArchivo')
    ruta = models.CharField(max_length=1024, blank=True, null=True, db_column='Ruta')
    tipo_mime = models.CharField(max_length=100, blank=True, null=True, db_column='TipoMime')
    tamano_bytes = models.BigIntegerField(blank=True, null=True, db_column='TamanoBytes')
    fecha_subida = models.DateTimeField(auto_now_add=True, db_column='FechaSubida')

    class Meta:
        db_table = 'Archivos'
        verbose_name = 'archivo'
        verbose_name_plural = 'archivos'

    def __str__(self):
        return self.nombre_archivo or f'Archivo #{self.id_archivo}'


# ---------------------------------------------------------------------------
# Logs, auditoría y notificaciones
# ---------------------------------------------------------------------------

class LogAcceso(models.Model):
    """Registro de accesos al sistema (éxito/fallo de login, IP, user-agent)."""
    id_log = models.BigAutoField(primary_key=True, db_column='IdLog')
    # SET_NULL conserva el log incluso si el usuario es eliminado.
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, blank=True, null=True, db_column='IdUsuario'
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, db_column='FechaHora')
    ip = models.CharField(max_length=50, blank=True, null=True, db_column='IP')
    user_agent = models.TextField(blank=True, null=True, db_column='UserAgent')
    resultado = models.CharField(max_length=50, blank=True, null=True, db_column='Resultado')

    class Meta:
        db_table = 'LogsAcceso'
        verbose_name = 'log de acceso'
        verbose_name_plural = 'logs de acceso'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f'Log #{self.id_log} ({self.resultado})'


class AuditCambio(models.Model):
    """Registro de auditoría para cambios sobre cualquier tabla del sistema."""
    id_audit = models.BigAutoField(primary_key=True, db_column='IdAudit')
    tabla = models.CharField(max_length=100, blank=True, null=True, db_column='Tabla')
    id_registro = models.CharField(max_length=100, blank=True, null=True, db_column='IdRegistro')
    # SET_NULL conserva la auditoría incluso si el usuario es eliminado.
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, blank=True, null=True, db_column='IdUsuario'
    )
    operacion = models.CharField(max_length=20, blank=True, null=True, db_column='Operacion')
    fecha_hora = models.DateTimeField(auto_now_add=True, db_column='FechaHora')
    detalle_antes = models.JSONField(blank=True, null=True, db_column='DetalleAntes')
    detalle_despues = models.JSONField(blank=True, null=True, db_column='DetalleDespues')

    class Meta:
        db_table = 'AuditCambios'
        verbose_name = 'registro de auditoría'
        verbose_name_plural = 'registros de auditoría'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f'Audit #{self.id_audit} — {self.tabla}.{self.operacion}'


class Notificacion(models.Model):
    """Notificación enviada a un usuario (push, in-app, etc.)."""
    id_notificacion = models.BigAutoField(primary_key=True, db_column='IdNotificacion')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario')
    tipo = models.CharField(max_length=50, blank=True, null=True, db_column='Tipo')
    contenido = models.TextField(blank=True, null=True, db_column='Contenido')
    leida = models.BooleanField(default=False, db_column='Leida')
    fecha_envio = models.DateTimeField(auto_now_add=True, db_column='FechaEnvio')

    class Meta:
        db_table = 'Notificaciones'
        verbose_name = 'notificación'
        verbose_name_plural = 'notificaciones'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f'Notif #{self.id_notificacion} para {self.id_usuario_id}'


# ---------------------------------------------------------------------------
# Tablas auxiliares
# ---------------------------------------------------------------------------

class TelefonoUsuario(models.Model):
    """
    Teléfonos adicionales de un usuario (múltiples por usuario).

    El campo InfoUsuario.telefono almacena el número de contacto principal;
    esta tabla permite registrar teléfonos secundarios con tipo y prioridad.
    """
    id_telefono = models.BigAutoField(primary_key=True, db_column='IdTelefono')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='IdUsuario')
    telefono = models.CharField(max_length=50, blank=True, null=True, db_column='Telefono')
    tipo = models.CharField(max_length=50, blank=True, null=True, db_column='Tipo')
    principal = models.BooleanField(default=False, db_column='Principal')

    class Meta:
        db_table = 'TelefonosUsuario'
        verbose_name = 'teléfono de usuario'
        verbose_name_plural = 'teléfonos de usuarios'

    def __str__(self):
        return f'{self.tipo}: {self.telefono} ({self.id_usuario_id})'


class TagDenuncia(models.Model):
    """Etiquetas libres para clasificar denuncias (ej. urgente, revisado)."""
    id_tag = models.AutoField(primary_key=True, db_column='IdTag')
    nombre_tag = models.CharField(max_length=100, unique=True, db_column='NombreTag')

    class Meta:
        db_table = 'TagsDenuncia'
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        ordering = ['nombre_tag']

    def __str__(self):
        return self.nombre_tag


class DenunciaTag(models.Model):
    """
    Relación muchos-a-muchos entre Denuncia y TagDenuncia.

    Al igual que UsuarioRol, Django no permite PK compuesta; se usa
    UniqueConstraint en (IdDenuncia, IdTag).
    """
    id_denuncia = models.ForeignKey(Denuncia, on_delete=models.CASCADE, db_column='IdDenuncia')
    id_tag = models.ForeignKey(TagDenuncia, on_delete=models.CASCADE, db_column='IdTag')

    class Meta:
        db_table = 'DenunciaTags'
        verbose_name = 'denuncia-tag'
        verbose_name_plural = 'denuncias-tags'
        constraints = [
            models.UniqueConstraint(fields=['id_denuncia', 'id_tag'], name='uq_dt_denuncia_tag'),
        ]

    def __str__(self):
        return f'Denuncia #{self.id_denuncia_id} + {self.id_tag_id}'


class PreferenciaUsuario(models.Model):
    """Preferencias de configuración por usuario (idioma, notificaciones, etc.)."""
    id_usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, primary_key=True, db_column='IdUsuario'
    )
    recibir_emails = models.BooleanField(default=True, db_column='RecibirEmails')
    idioma = models.CharField(max_length=10, default='es', db_column='Idioma')
    zona_horaria = models.CharField(max_length=50, blank=True, null=True, db_column='ZonaHoraria')

    class Meta:
        db_table = 'PreferenciasUsuario'
        verbose_name = 'preferencias de usuario'
        verbose_name_plural = 'preferencias de usuarios'

    def __str__(self):
        return f'Prefs de {self.id_usuario}'
