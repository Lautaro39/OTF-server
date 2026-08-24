# OTF Server - Configuración e Instalación

Este repositorio contiene el backend para el proyecto OTF, construido con **Django** y **Django REST Framework (DRF)**, utilizando **PostgreSQL** como base de datos.

A continuación se detallan los pasos necesarios para configurar y poner en marcha el servidor de desarrollo local.

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:
1. **Python** (versión 3.10 o superior recomendada).
2. **PostgreSQL** (activo y accesible localmente).

---

## Método Rápido (Recomendado)

Hemos creado un script de automatización (`start.sh`) en la raíz del proyecto `OTF-server` que se encarga de crear el entorno virtual, instalar dependencias, correr las migraciones, sembrar datos de prueba (categorías y estados) e iniciar el servidor.

Para usarlo, simplemente ejecuta en tu terminal:
```bash
./start.sh
```

---

## Pasos Manuales para la Configuración

Si prefieres realizar el proceso de forma manual, sigue estos pasos:

### 1. Clonar el repositorio y posicionarse en la carpeta raíz
Abre una terminal en la raíz del proyecto `OTF-server`:
```bash
cd OTF-server
```

### 2. Configurar Firebase Admin SDK (Para Notificaciones)
Para que el sistema de notificaciones push funcione:
1. Genera una nueva clave privada desde la consola de Firebase.
2. Descarga el archivo JSON y muévelo al directorio `backend_otf/` con el nombre de **`serviceAccountKey.json`**.
*Nota: Este archivo también está ignorado en Git por motivos de seguridad.*

### 3. Crear y activar un Entorno Virtual (Virtualenv)
* **En macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* **En Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

### 4. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar la Base de Datos PostgreSQL
Debes tener PostgreSQL activo y crear la base de datos:
```sql
CREATE DATABASE backend_otf;
CREATE USER backend_otf WITH PASSWORD 'backend_otf';
GRANT ALL PRIVILEGES ON DATABASE backend_otf TO backend_otf;
```

### 6. Ejecutar Migraciones y Seeds
Múevete al directorio `backend_otf` y ejecuta:
```bash
cd backend_otf
python manage.py migrate
python manage.py seed
python seed_comunidad.py
```

### 7. Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver 0.0.0.0:8000
```
El servidor estará corriendo en `http://localhost:8000/`.

