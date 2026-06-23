from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.db.models import Count
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import (
    Archivo,
    AsistenciaEvento,
    AvisoServicio,
    CarpetaArchivo,
    Categoria,
    Denuncia,
    Estado,
    EventoComunidad,
    InfoUsuario,
    Voto,
    Equipo,
    MiembroEquipo,
)
from .serializers import (
    AdminDenunciaSerializer,
    EquipoSerializer,
    ArchivoSerializer,
    AvisoServicioSerializer,
    CategoriaSerializer,
    DenunciaDetailSerializer,
    DenunciaListSerializer,
    DenunciaWriteSerializer,
    EstadoSerializer,
    EventoComunidadSerializer,
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
        if not serializer.is_valid():
            print("VALIDATION ERRORS IN REGISTER:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
        if not serializer.is_valid():
            print("VALIDATION ERRORS IN DENUNCIA CREATE:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
    serializer_class = ArchivoSerializer

    def get_queryset(self):
        qs = Archivo.objects.select_related('id_carpeta__id_denuncia')
        denuncia_id = self.request.query_params.get('denuncia')
        if denuncia_id:
            qs = qs.filter(id_carpeta__id_denuncia_id=denuncia_id)
        return qs

    def perform_create(self, serializer):
        denuncia_id = serializer.validated_data.pop('id_denuncia')
        denuncia = Denuncia.objects.get(id_denuncia=denuncia_id)
        carpeta, _ = CarpetaArchivo.objects.get_or_create(
            id_denuncia=denuncia,
            defaults={'nombre_carpeta': 'Principal'},
        )
        serializer.save(id_carpeta=carpeta)

    def perform_destroy(self, instance):
        denuncia = instance.id_carpeta.id_denuncia
        if denuncia.id_usuario_id != self.request.user.id:
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


class AvisoServicioViewSet(viewsets.ModelViewSet):
    serializer_class = AvisoServicioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return AvisoServicio.objects.all()
        return AvisoServicio.objects.filter(activo=True)


class EventoComunidadViewSet(viewsets.ModelViewSet):
    serializer_class = EventoComunidadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EventoComunidad.objects.annotate(
            asistentes_count=Count('asistentes')
        ).order_by('fecha_evento')

    @action(detail=True, methods=['post'], url_path='asistir')
    def asistir(self, request, pk=None):
        evento = self.get_object()
        user = request.user
        
        # Toggle attendance
        asistencia, created = AsistenciaEvento.objects.get_or_create(
            id_usuario=user, id_evento=evento
        )
        if not created:
            # Already exists, so unregister (toggle off)
            asistencia.delete()
            is_attending = False
        else:
            is_attending = True
            
        # Get updated count of attendees
        asistentes_count = evento.asistentes.count()
        return Response({
            'is_attending': is_attending,
            'asistentes_count': asistentes_count
        })


class AdminReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminDenunciaSerializer

    def get_queryset(self):
        if not self.request.user.is_staff:
            return Denuncia.objects.none()
        
        ordering = self.request.query_params.get('ordering', 'latest')
        qs = Denuncia.objects.select_related(
            'id_usuario__infousuario',
            'id_categoria',
            'estado_actual',
            'master_case'
        )
        
        if ordering == 'oldest':
            qs = qs.order_by('fecha_creacion')
        else: # latest
            qs = qs.order_by('-fecha_creacion')
            
        return qs

    @action(detail=True, methods=['patch'], url_path='assign')
    def assign(self, request, pk=None):
        denuncia = self.get_object()
        team_id = request.data.get('equipo_asignado')
        
        estado_proceso, _ = Estado.objects.get_or_create(nombre_estado='En Proceso')
        denuncia.estado_actual = estado_proceso
        denuncia.equipo_asignado_id = team_id
        denuncia.save()
        
        serializer = self.get_serializer(denuncia)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='resolve')
    def resolve(self, request, pk=None):
        denuncia = self.get_object()
        
        estado_completa, _ = Estado.objects.get_or_create(nombre_estado='Completa')
        denuncia.estado_actual = estado_completa
        denuncia.save()
        
        serializer = self.get_serializer(denuncia)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='discard')
    def discard(self, request, pk=None):
        denuncia = self.get_object()
        
        estado_descartada, _ = Estado.objects.get_or_create(nombre_estado='Descartada')
        denuncia.estado_actual = estado_descartada
        denuncia.save()
        
        serializer = self.get_serializer(denuncia)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='merge')
    def merge_reports(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No ids provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Convert IDs to integer (since Django uses integer primary keys)
        try:
            int_ids = [int(x) for x in ids]
        except ValueError:
            return Response({'error': 'Invalid IDs format'}, status=status.HTTP_400_BAD_REQUEST)
            
        matching_reports = list(Denuncia.objects.filter(id_denuncia__in=int_ids).order_by('fecha_creacion'))
        if not matching_reports:
            return Response({'error': 'No matching reports found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Oldest report is the master
        master = matching_reports[0]
        
        # Update all other reports to have master_case set to master
        for r in matching_reports[1:]:
            r.master_case = master
            r.save()
            
        return Response({'success': True, 'master_id': master.id_denuncia})


class EquipoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EquipoSerializer

    def get_queryset(self):
        if not self.request.user.is_staff:
            return Equipo.objects.none()
            
        qs = Equipo.objects.all().prefetch_related('miembros').select_related('id_categoria')
        
        # Filter by category name if provided (e.g. GET /api/equipos/?categoria=Alumbrado)
        categoria_name = self.request.query_params.get('categoria')
        if categoria_name:
            qs = qs.filter(id_categoria__nombre=categoria_name)
            
        return qs

    def perform_create(self, serializer):
        categoria = serializer.validated_data['id_categoria']
        num_equipos = Equipo.objects.filter(id_categoria=categoria).count() + 1
        nombre = f"Grupo {categoria.nombre} {num_equipos}"
        serializer.save(nombre=nombre)
