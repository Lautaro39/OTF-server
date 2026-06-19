from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

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

admin.site.register(Administrador)
admin.site.register(Archivo)
admin.site.register(AuditCambio)
admin.site.register(CarpetaArchivo)
admin.site.register(Categoria)
admin.site.register(Denuncia)
admin.site.register(DenunciaTag)
admin.site.register(Estado)
admin.site.register(EstadoDenuncia)
admin.site.register(InfoUsuario)
admin.site.register(LogAcceso)
admin.site.register(Notificacion)
admin.site.register(PreferenciaUsuario)
admin.site.register(Rol)
admin.site.register(TagDenuncia)
admin.site.register(TelefonoUsuario)
admin.site.register(UsuarioRol)
admin.site.register(Voto)

admin.site.register(Usuario, DjangoUserAdmin)
