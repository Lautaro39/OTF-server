from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArchivoViewSet,
    CategoriaViewSet,
    DenunciaViewSet,
    EstadoViewSet,
    VotoViewSet,
)

router = DefaultRouter()
router.register(r'denuncias', DenunciaViewSet, basename='denuncia')
router.register(r'votos', VotoViewSet, basename='voto')
router.register(r'archivos', ArchivoViewSet, basename='archivo')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'estados', EstadoViewSet, basename='estado')

urlpatterns = [
    path('', include(router.urls)),
]
