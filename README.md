# Gestor de tareas

Aplicación web de gestión de tareas construida con Django y Django REST Framework. Incluye autenticación mediante JSON Web Tokens (JWT), una interfaz HTML para el registro y el inicio de sesión, y una API REST para la administración de usuarios y tareas.

## 1. Información general

| Concepto | Detalle |
| --- | --- |
| Lenguaje | Python 3.15.2 |
| Framework | Django 6.1.2 |
| API | Django REST Framework 3.18.3 |
| Autenticación | SimpleJWT 5.5.1 |
| Base de datos | SQLite (`db.sqlite3`) |
| Idioma de la interfaz | Español |

La solución se organiza en dos paquetes:

- `gestor_tareas/`: configuración del proyecto, enrutado raíz y puntos de entrada WSGI/ASGI.
- `tareas/`: aplicación única. Contiene modelos, serializadores, vistas, permisos, plantillas, JavaScript y pruebas.

## 2. Requisitos previos

- Python 3.15.2 disponible en el sistema.
- Acceso a terminal con PowerShell (Windows).

## 3. Instalación

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Todos los comandos de administración de Django de este documento deben ejecutarse con el intérprete del entorno virtual: `.\venv\Scripts\python.exe`.

## 4. Base de datos y migraciones

La base de datos `db.sqlite3` se encuentra versionada en el repositorio. Incluye cuentas de prueba para desarrollo y es compartida por las ejecuciones locales.

Migraciones de la aplicación `tareas`:

| Migración | Descripción |
| --- | --- |
| `0001_initial` | Crea los modelos `Usuario` y `Tarea`. |
| `0002_usuario_nombre_completo` | Añade `Usuario.nombre_completo`, campo no único que almacena el nombre ingresado en el formulario. |

Antes de aplicar migraciones sobre una base de datos compartida se recomienda realizar una copia de seguridad de `db.sqlite3`. La migración `0002` es aditiva: conserva los usuarios existentes y sus contraseñas.

El modelo `Usuario` extiende `AbstractUser` y añade el campo `rol` (`administrador` o `usuario`). La autorización se basa en este campo, no en los permisos internos de Django.

## 5. Ejecución

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

Interfaz web: <http://localhost:8000/>

## 6. Credenciales de prueba

| Uso | Usuario | Contraseña | Rol |
| --- | --- | --- | --- |
| Administración | `admin` | `admin` | `administrador` |
| Usuario estándar | `usuario2` | `usuario2` | `usuario` |

La cuenta `admin` se recrea automáticamente en cada ejecución de `migrate` mediante una señal `post_migrate`. La cuenta `usuario2` existe únicamente en la base de datos de desarrollo versionada.

El archivo `.gitignore` mantiene comentada la línea `db.sqlite3`, por lo que la base de datos se versiona junto con el código. Si se desea conservar una base de datos propia, debe añadirse dicha línea al ignore.

## 7. Registro de usuarios (CU-01)

El formulario de registro (`/registro/`) contiene exactamente tres campos: nombre completo, correo electrónico y contraseña. Envía los datos mediante `fetch` a `POST /api/register/`.

### 7.1. Reglas de validación

| Regla | Comportamiento |
| --- | --- |
| Nombre completo | Obligatorio. Se almacena en `nombre_completo`, que **admite valores repetidos**. |
| Correo electrónico | Obligatorio, con formato válido y único sin distinguir mayúsculas de minúsculas. |
| Contraseña | Obligatoria, de 8 a 20 caracteres, incluidos ambos extremos. Se almacena con el hash de Django. |
| Errores | Si fallan varios campos, se devuelven todos en la misma respuesta. |
| Disponibilidad del correo | Solo se comprueba cuando los tres campos superan su validación. |
| Creación | La cuenta se crea únicamente si todas las validaciones son correctas. |

### 7.2. Nombre completo e identificador interno

El campo `username` de la petición contiene el **nombre completo** (por ejemplo, `José Pérez`). El sistema lo guarda literalmente en `nombre_completo` y genera el `username` interno necesario para autenticarse:

- El primer usuario con ese nombre conserva `José Pérez` como identificador.
- Los siguientes reciben un sufijo numérico: `José Pérez_2`, `José Pérez_3`, etc.

De este modo, varios usuarios pueden compartir nombre completo siempre que utilicen correos distintos, sin comprometer la unicidad del identificador de Django ni el inicio de sesión JWT.

### 7.3. Ejemplo de petición y respuesta

Petición:

```http
POST /api/register/
Content-Type: application/json

{
  "username": "José Pérez",
  "email": "jose.cp02@gmail.com",
  "password": "ClaveSegura123!"
}
```

Respuesta correcta (HTTP 201):

```json
{
  "mensaje": "Registro exitoso.",
  "usuario": {
    "id": 12,
    "nombre_completo": "José Pérez",
    "username": "José Pérez",
    "rol": "usuario"
  }
}
```

Respuesta con errores (HTTP 400):

```json
{
  "username": ["Este campo no puede estar en blanco."],
  "email": ["Introduzca una dirección de correo electrónico válida."],
  "password": ["La contraseña debe tener al menos 8 caracteres."]
}
```

La contraseña nunca se incluye en la respuesta. El identificador `username` se devuelve porque es necesario para iniciar sesión.

## 8. Endpoints de la API

Todas las rutas están bajo el prefijo `/api/`, salvo las indicadas como rutas raíz.

### Autenticación

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/api/token/` | Obtención de tokens JWT (SimpleJWT). |
| POST | `/api/token/refresh/` | Renovación del token de acceso. |
| POST | `/api/login/` | Inicio de sesión personalizado; devuelve tokens y datos del usuario. |
| POST | `/api/logout/` | Invalidación del token de actualización. |
| GET | `/api/perfil/` | Datos del usuario autenticado. |

La configuración JWT utiliza tokens de acceso de 15 minutos y de actualización de 1 día, con rotación y lista negra activadas. El cliente web almacena los tokens en `localStorage`, renueva el access token una sola vez ante un 401 y blacklistea el refresh token al cerrar sesión.

### Administración de usuarios

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/admin/usuarios/` | Listado de usuarios (solo administradores). |
| GET, PATCH | `/api/admin/usuarios/<id>/` | Consulta y modificación de rol o estado. |
| GET | `/api/admin-restringido/` | Endpoint de ejemplo exclusivo para administradores. |

### Tareas

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET, POST | `/api/tareas/` | Listado y creación de tareas. |
| GET, PUT, PATCH, DELETE | `/api/tareas/<id>/` | Detalle, modificación y eliminación. |

Los administradores ven todas las tareas y pueden asignarlas a usuarios activos mediante `usuario_id`. Los usuarios estándar solo ven y gestionan sus propias tareas.

### Pantallas HTML

| Ruta | Descripción |
| --- | --- |
| `/` | Inicio de sesión. |
| `/registro/` | Registro de usuarios. |
| `/tareas/` | Listado de tareas. |
| `/api/perfil-vista/` | Perfil del usuario. |

## 9. Pruebas automatizadas

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test
```

La suite completa consta de **54 pruebas**:

| Archivo | Pruebas | Contenido |
| --- | --- | --- |
| `tareas/tests.py` | 19 | Administración de usuarios, registro y permisos de tareas. |
| `tareas/tests_cu01.py` | 35 | 27 casos del CU-01 (CP-01 a CP-27) y 8 pruebas de compatibilidad. |

Las pruebas se ejecutan sobre una base de datos de prueba aislada; no modifican `db.sqlite3`. Django escribe el progreso en `stderr`, por lo que en PowerShell puede aparecer un estilo de error aunque el resultado final sea `OK`. Debe verificarse la línea `OK`, no el formato del mensaje.

## 10. Preparación para la ejecución secuencial del CU-01

Los casos del CU-01 se ejecutan de forma secuencial sobre una base de datos compartida. Para evitar resultados incorrectos:

1. Partir de una copia limpia y migrada de `db.sqlite3`.
2. Crear una única vez la cuenta previa requerida por CP-12 y CP-24, con un identificador distinto:

   ```text
   username: cuenta_previa_cu01
   email:    jose@gmail.com
   password: ClaveSegura123!
   rol:      usuario
   ```

3. Restaurar la copia limpia antes de cada ejecución completa de los 27 casos. De lo contrario, los correos `jose.cpNN@gmail.com` generados en una pasada anterior provocarían un rechazo por correo duplicado.
4. No añadir usuarios de prueba en `apps.py`, en señales `post_migrate` ni directamente en la base de datos de producción.

## 11. Configuración adicional

- Idioma: `es`; zona horaria: `UTC`.
- Backend de correo: consola (los mensajes se imprimen en la terminal; no se envía correo real).
- El panel de administración está disponible en `/admin/`.
