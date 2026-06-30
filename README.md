# OTF Server - Configuración e Instalación

Este repositorio contiene el backend para el proyecto OTF, construido con **Django** y **Django REST Framework (DRF)**, utilizando **PostgreSQL** como base de datos.

A continuación se detallan los pasos necesarios para configurar y poner en marcha el servidor de desarrollo local.

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:
1. **Python** (versión 3.10 o superior recomendada).
2. **PostgreSQL** (activo y accesible localmente).

---

## Pasos para la Configuración

### 1. Clonar el repositorio y posicionarse en la carpeta raíz
Abre una terminal en la raíz del proyecto `OTF-server`:
```bash
cd OTF-server
```

### 2. Crear y activar un Entorno Virtual (Virtualenv)
Es recomendable aislar las dependencias del proyecto.

* **En Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

* **En macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar las dependencias
Con el entorno virtual activo, instala los paquetes necesarios detallados en el archivo `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Configurar la Base de Datos PostgreSQL
Debes tener una instancia de PostgreSQL ejecutándose y crear una base de datos con las credenciales indicadas en el archivo de entorno. 

Por defecto, el archivo `backend_otf/.env` tiene la siguiente configuración:
* **Base de Datos:** `backend_otf`
* **Usuario:** `backend_otf`
* **Contraseña:** `backend_otf`
* **Host:** `localhost`
* **Puerto:** `5432`

Puedes crear la base de datos y el usuario ejecutando los siguientes comandos en tu terminal interactiva de PostgreSQL (`psql` o mediante pgAdmin):
```sql
CREATE DATABASE backend_otf;
CREATE USER backend_otf WITH PASSWORD 'backend_otf';
GRANT ALL PRIVILEGES ON DATABASE backend_otf TO backend_otf;
```

### 5. Navegar a la carpeta del backend
Para ejecutar comandos de Django, muévete al directorio `backend_otf` (donde está el archivo `manage.py`):
```bash
cd backend_otf
```

### 6. Ejecutar las Migraciones
Crea las tablas en la base de datos a partir de los modelos de Django:
```bash
python manage.py migrate
```

### 7. Iniciar el Servidor de Desarrollo
Una vez configurado todo, inicia el servidor local de Django:
```bash
python manage.py runserver
```

El servidor estará corriendo en `http://127.0.0.1:8000/`.
