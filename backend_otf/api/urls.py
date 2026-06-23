from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminReportViewSet,
    ArchivoViewSet,
    AvisoServicioViewSet,
    CategoriaViewSet,
    DenunciaViewSet,
    EstadoViewSet,
    EventoComunidadViewSet,
    VotoViewSet,
    EquipoViewSet,
)

router = DefaultRouter()
router.register(r'denuncias', DenunciaViewSet, basename='denuncia')
router.register(r'votos', VotoViewSet, basename='voto')
router.register(r'archivos', ArchivoViewSet, basename='archivo')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'estados', EstadoViewSet, basename='estado')
router.register(r'avisos', AvisoServicioViewSet, basename='aviso')
router.register(r'eventos', EventoComunidadViewSet, basename='evento')
router.register(r'admin/reports', AdminReportViewSet, basename='admin-report')
router.register(r'equipos', EquipoViewSet, basename='equipo')

urlpatterns = [
    path('', include(router.urls)),
]
