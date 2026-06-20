from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import (
    Archivo,
    CarpetaArchivo,
    Categoria,
    Denuncia,
    Estado,
    InfoUsuario,
    Voto,
)
from .serializers import (
    CategoriaSerializer,
    DenunciaDetailSerializer,
    DenunciaListSerializer,
    DenunciaWriteSerializer,
    EstadoSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserResponseSerializer,
    VotoSerializer,
)


# =========================================================================
# Auth views
# =========================================================================


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return Response({'error': 'Credenciales invalidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserResponseSerializer(user, context={'request': request}).data,
            'token': token.key,
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserResponseSerializer(user, context={'request': request}).data,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        if str(request.user.id) != str(pk):
            return Response({'error': 'No autorizado.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.update(request.user, serializer.validated_data)
        return Response(UserResponseSerializer(user, context={'request': request}).data)


# =========================================================================
# Denuncia ViewSet
# =========================================================================


class DenunciaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Denuncia.objects.select_related(
            'id_usuario', 'id_categoria', 'estado_actual'
        )
        if self.action in ['update', 'partial_update', 'destroy']:
            return qs.filter(id_usuario=self.request.user)
        return qs.filter(id_usuario=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DenunciaWriteSerializer
        if self.action == 'list':
            return DenunciaListSerializer
        return DenunciaDetailSerializer

    def perform_create(self, serializer):
        estado_pendiente = Estado.objects.filter(nombre_estado='Pendiente').first()
        serializer.save(id_usuario=self.request.user, estado_actual=estado_pendiente)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        detail_serializer = DenunciaDetailSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# =========================================================================
# Voto ViewSet
# =========================================================================


class VotoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = VotoSerializer

    def get_queryset(self):
        qs = Voto.objects.select_related('id_usuario')
        denuncia_id = self.request.query_params.get('denuncia')
        if denuncia_id:
            qs = qs.filter(id_denuncia_id=denuncia_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(id_usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {'error': 'Ya has votado en esta denuncia.'},
                status=status.HTTP_409_CONFLICT,
            )

    def perform_destroy(self, instance):
        if instance.id_usuario != self.request.user:
            raise PermissionError()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id_usuario != request.user:
            return Response(
                {'error': 'No puedes eliminar el voto de otro usuario.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


# =========================================================================
# Archivo ViewSet
# =========================================================================


class ArchivoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Archivo.objects.select_related('id_carpeta__id_denuncia')

    def perform_create(self, serializer):
        denuncia_id = self.request.data.get('id_denuncia')
        if not denuncia_id:
            raise serializers.ValidationError({'id_denuncia': 'Requerido.'})

        denuncia = Denuncia.objects.get(id_denuncia=denuncia_id)
        carpeta, _ = CarpetaArchivo.objects.get_or_create(
            id_denuncia=denuncia,
            defaults={'nombre_carpeta': 'Principal'},
        )
        serializer.save(id_carpeta=carpeta)

    def perform_destroy(self, instance):
        denuncia = instance.id_carpeta.id_denuncia
        if denuncia.id_usuario != self.request.user:
            raise PermissionError()
        instance.delete()


# =========================================================================
# Catalogo ViewSets (read-only)
# =========================================================================


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]


class EstadoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    permission_classes = [AllowAny]
