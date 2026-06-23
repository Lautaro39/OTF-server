# Guía de Instrucciones de Modificaciones - Backend OTF-server

Este documento contiene las instrucciones paso a paso que un agente de IA o desarrollador debe seguir para reproducir exactamente todas las modificaciones y correcciones aplicadas en el backend Django (`OTF-server`).

---

## 🐍 Modificaciones en el Backend (`OTF-server`)

### Paso 1: Habilitar CRUD de Avisos y Eventos
1. Abre [`backend_otf/api/views.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/api/views.py).
2. Cambia la clase base de `AvisoServicioViewSet` de `viewsets.ReadOnlyModelViewSet` a `viewsets.ModelViewSet`.
3. Cambia la clase base de `EventoComunidadViewSet` de `viewsets.ReadOnlyModelViewSet` a `viewsets.ModelViewSet`.
4. En `AvisoServicioViewSet.get_queryset()`, implementa una validación para que si el usuario es administrador (`self.request.user.is_staff`), retorne todos los avisos (activos e inactivos), y si es un usuario común de la app móvil, solo retorne los activos:
   ```python
   def get_queryset(self):
       if self.request.user and self.request.user.is_staff:
           return AvisoServicio.objects.all()
       return AvisoServicio.objects.filter(activo=True)
   ```

### Paso 2: Instalar y Configurar CORS para Flutter Web
1. Abre [`requirements.txt`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/requirements.txt) y añade al final la librería:
   ```text
   django-cors-headers
   ```
   Instálala en el entorno virtual ejecutando: `.venv\Scripts\pip install -r requirements.txt`.
2. Abre [`backend_otf/backend_otf/settings.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/backend_otf/settings.py) y realiza los siguientes cambios:
   * Añade `'corsheaders'` a la lista de `INSTALLED_APPS` (justo encima de `'api'`).
   * Añade `'corsheaders.middleware.CorsMiddleware'` a la lista de `MIDDLEWARE` (preferiblemente al principio del arreglo, antes de `CommonMiddleware`).
   * Al final del archivo, añade la bandera para permitir peticiones de origen cruzado:
     ```python
     CORS_ALLOW_ALL_ORIGINS = True
     ```

### Paso 3: Exponer Datos de Administrador en el Serializador de Login
1. Abre [`backend_otf/api/serializers.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/api/serializers.py).
2. Modifica la clase `UserResponseSerializer` para que incluya los campos de `legajo` y `area`, resolviéndolos a través de la relación 1:1 con el modelo `Administrador`:
   ```python
   class UserResponseSerializer(serializers.ModelSerializer):
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

       # ... (mantener getters de phone, dni e image) ...

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
   ```

### Paso 4: Extensión del Modelo Denuncia y Migraciones
1. Abre [`backend_otf/api/models.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/api/models.py).
2. Añade los siguientes campos al final del modelo `Denuncia` (justo debajo de `estado_actual`):
   ```python
   equipo_asignado = models.IntegerField(blank=True, null=True, db_column='EquipoAsignado')
   master_case = models.ForeignKey(
       'self',
       on_delete=models.SET_NULL,
       blank=True,
       null=True,
       db_column='MasterCaseId',
       related_name='duplicados',
   )
   ```
3. Genera y aplica las migraciones de base de datos desde la consola:
   ```bash
   .venv\Scripts\python.exe backend_otf\manage.py makemigrations
   .venv\Scripts\python.exe backend_otf\manage.py migrate
   ```

### Paso 5: Crear Endpoints de Gestión de Denuncias
1. Abre [`backend_otf/api/serializers.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/api/serializers.py) y añade el serializador para la visualización de denuncias en el panel de administración:
   ```python
   class AdminDenunciaSerializer(serializers.ModelSerializer):
       id = serializers.IntegerField(source='id_denuncia', read_only=True)
       categoria = serializers.CharField(source='id_categoria.nombre', allow_null=True, required=False)
       foto_url = serializers.SerializerMethodField()
       estado = serializers.CharField(source='estado_actual.nombre_estado', allow_null=True, required=False)
       master_case_id = serializers.PrimaryKeyRelatedField(source='master_case', read_only=True)
       creador_dni = serializers.SerializerMethodField()

       class Meta:
           model = Denuncia
           fields = [
               'id', 'categoria', 'descripcion', 'foto_url', 'direccion', 
               'latitud', 'longitud', 'fecha_creacion', 'estado', 
               'equipo_asignado', 'master_case_id', 'creador_dni'
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
   ```
2. Abre [`backend_otf/api/views.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/api/views.py):
   * Importa `AdminDenunciaSerializer` desde `.serializers`.
   * Implementa la clase `AdminReportViewSet` para responder a las acciones de las bandejas del administrador:
     ```python
     class AdminReportViewSet(viewsets.ModelViewSet):
         permission_classes = [IsAuthenticated]
         serializer_class = AdminDenunciaSerializer

         def get_queryset(self):
             if not self.request.user.is_staff:
                 return Denuncia.objects.none()
             ordering = self.request.query_params.get('ordering', 'latest')
             qs = Denuncia.objects.select_related(
                 'id_usuario__infousuario', 'id_categoria', 'estado_actual', 'master_case'
             )
             return qs.order_by('fecha_creacion' if ordering == 'oldest' else '-fecha_creacion')

         @action(detail=True, methods=['patch'], url_path='assign')
         def assign(self, request, pk=None):
             denuncia = self.get_object()
             team_number = request.data.get('equipo_asignado')
             denuncia.estado_actual, _ = Estado.objects.get_or_create(nombre_estado='En Proceso')
             denuncia.equipo_asignado = team_number
             denuncia.save()
             return Response(self.get_serializer(denuncia).data)

         @action(detail=True, methods=['patch'], url_path='resolve')
         def resolve(self, request, pk=None):
             denuncia = self.get_object()
             denuncia.estado_actual, _ = Estado.objects.get_or_create(nombre_estado='Completa')
             denuncia.save()
             return Response(self.get_serializer(denuncia).data)

         @action(detail=True, methods=['patch'], url_path='discard')
         def discard(self, request, pk=None):
             denuncia = self.get_object()
             denuncia.estado_actual, _ = Estado.objects.get_or_create(nombre_estado='Descartada')
             denuncia.save()
             return Response(self.get_serializer(denuncia).data)

         @action(detail=False, methods=['post'], url_path='merge')
         def merge_reports(self, request):
             ids = request.data.get('ids', [])
             if not ids:
                 return Response({'error': 'No ids provided'}, status=400)
             try:
                 int_ids = [int(x) for x in ids]
             except ValueError:
                 return Response({'error': 'Invalid IDs format'}, status=400)
             matching_reports = list(Denuncia.objects.filter(id_denuncia__in=int_ids).order_by('fecha_creacion'))
             if not matching_reports:
                 return Response({'error': 'No matching reports found'}, status=404)
             master = matching_reports[0]
             for r in matching_reports[1:]:
                 r.master_case = master
                 r.save()
             return Response({'success': True, 'master_id': master.id_denuncia})
     ```
3. Abre [`backend_otf/api/urls.py`](file:///C:/Users/PedroxVA/ProyectosUNSA/OTF/OTF-server/backend_otf/api/urls.py) e importa `AdminReportViewSet` para registrar la ruta en el router:
   ```python
   router.register(r'admin/reports', AdminReportViewSet, basename='admin-report')
   ```
