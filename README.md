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

Las versiones indicadas corresponden al entorno en el que se ejecutaron las pruebas documentadas; describen ese entorno, no imponen actualizaciones de dependencias. La versión de Selenium se detalla en la sección 12.2.

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

> **Advertencia:** las pruebas Selenium crean usuarios reales en `db.sqlite3`. No deben ejecutarse contra una base de datos de producción. Realice una copia de seguridad antes de la ejecución y revise los registros afectados antes de cualquier limpieza.

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

> **Advertencia:** estas credenciales son exclusivas de desarrollo y pruebas. No deben utilizarse en un entorno de producción.

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

El campo `username` de la petición contiene el **nombre completo** (por ejemplo, `José Pérez`). `RegistroSerializer` guarda ese valor literalmente en `Usuario.nombre_completo` y genera por separado el `username` interno que Django usa para autenticar:

- Se parte del nombre completo sin espacios sobrantes (limitado a 150 caracteres) como base del identificador.
- Si esa base ya está ocupada, se prueba `José Pérez_1`, luego `José Pérez_2`, y así sucesivamente hasta encontrar un valor libre.
- El texto también se divide en `first_name` y `last_name` para conservar los campos nativos de `AbstractUser`.

Por ejemplo, si ya existen `José Pérez` y `José Pérez_1`, el siguiente registro con ese mismo nombre completo obtendrá el identificador interno `José Pérez_2`. El campo `nombre_completo` **no es único** y puede repetirse; el `username` interno **sí es único** y es el que se utiliza para iniciar sesión. Esta separación está implementada en `RegistroSerializer._generar_username()` y `RegistroSerializer.create()`.

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
    "username": "José Pérez_2",
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

La contraseña nunca se incluye en la respuesta. El identificador `username` se devuelve porque es necesario para iniciar sesión. Los valores de `id` y de `username` del ejemplo son ilustrativos: el sufijo real depende de los identificadores ya ocupados en la base de datos.

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

Las pruebas de Django se ejecutan sobre una base de datos de prueba aislada; no modifican `db.sqlite3`. Django escribe el progreso en `stderr`, por lo que en PowerShell puede aparecer un estilo de error aunque el resultado final sea `OK`. Debe verificarse la línea `OK`, no el formato del mensaje.

El módulo `selenium_tests/test_selenium.py` no ejecuta nada al ser importado: la batería sólo arranca al invocarlo como programa. Por eso no interfiere con `manage.py test`. Su uso se describe en la sección 12.

## 10. Preparación para la ejecución secuencial del CU-01

Los casos del CU-01 se ejecutan de forma secuencial sobre la base de datos del servidor. Para evitar resultados incorrectos:

1. Los correos de los **casos aceptados** reciben un sufijo único por ejecución (`sel_AAAAMMDDHHMMSS_xxxxxx`), por lo que no es necesario restaurar una copia limpia entre pasadas.
2. Crear **una sola vez** la cuenta previa requerida por CP-12 y CP-24:

   ```powershell
   .\venv\Scripts\python.exe -m selenium_tests.preparar_base
   ```

   El script es idempotente: si `jose@gmail.com` ya existe, lo conserva sin modificar contraseñas, roles ni estados, y no escribe marcador alguno. La cuenta que crea cuando no existe es:

   ```text
   username: cuenta_previa_cu01
   email:    jose@gmail.com
   contraseña de prueba: Ab1!Ab1!Ab1!
   rol:      usuario
   ```

   Cuando el script crea la cuenta, guarda su identificador en `selenium_tests/.cuenta_previa_generada.txt` (archivo ignorado por Git). Ese marcador es la única forma en que la limpieza puede distinguirla de una cuenta `jose@gmail.com` que ya existiera antes de preparar las pruebas.

3. Para limpiar las cuentas generadas por la batería, ejecute primero la simulación, que sólo muestra información:

   ```powershell
   .\venv\Scripts\python.exe -m selenium_tests.limpiar_datos_prueba
   ```

   El programa muestra por separado las cuentas que se eliminarían y las que se conservan, incluidos los administradores y los usuarios ajenos a las pruebas.

   > **ADVERTENCIA:** el siguiente comando elimina definitivamente las cuentas listadas en la simulación. Ejecútelo sólo después de revisar esa lista.

   ```powershell
   .\venv\Scripts\python.exe -m selenium_tests.limpiar_datos_prueba --confirmar
   ```

   Sólo elimina correos con el formato exacto `jose.cpNN+sel_AAAAMMDDHHMMSS_xxxxxx@gmail.com` generados por la batería y, si existe el marcador, la cuenta previa creada por `preparar_base.py`. No elimina coincidencias parciales, administradores ni usuarios normales no generados por Selenium.
4. No añadir usuarios de prueba en `apps.py`, en señales `post_migrate` ni en el funcionamiento normal de la aplicación.
5. Antes de ejecutar por primera vez, guarde una copia de `db.sqlite3` fuera del repositorio. Los casos aceptados crean usuarios reales en esa base de datos y la limpieza debe realizarse únicamente después de revisar los registros afectados.

## 11. Configuración adicional

- Idioma: `es`; zona horaria: `UTC`.
- Backend de correo: consola (los mensajes se imprimen en la terminal; no se envía correo real).
- El panel de administración está disponible en `/admin/`.

## 12. Automatización de pruebas con Selenium (CU-01)

### 12.1. Descripción general

La carpeta `selenium_tests/` contiene la automatización de los **27 casos de prueba del caso de uso CU-01: Registro de usuarios**, organizados según las técnicas de caja negra de la Unidad 2: particiones de equivalencia (CP-01 a CP-12), valores límite (CP-13 a CP-18) y causa-efecto (CP-19 a CP-27).

Cada caso abre el formulario en Chrome, completa los tres campos, pulsa "Crear cuenta", espera el mensaje de la aplicación y comprueba:

- que aparezca el mensaje de éxito o de error correspondiente;
- qué campo o campos se informan como inválidos, leyendo el texto `campo: mensaje` que genera el JavaScript de la plantilla;
- que se haya creado (o no) el usuario en la base de datos, consultando el ORM de Django.

Los valores de entrada proceden de la planilla original implementada en `tareas/tests_cu01.py` (por ejemplo, `José Pérez`, `jose@gmail`, contraseñas de 5, 7, 8, 9, 19, 20, 21 y 23 caracteres).

### 12.2. Herramientas utilizadas

| Herramienta | Versión comprobada | Función |
| --- | --- | --- |
| Python | 3.15.2 | Lenguaje de la automatización. |
| Selenium WebDriver | 4.53.0 | Control del navegador. |
| Google Chrome for Testing | 158.0.8127.36 | Navegador real donde se ejecuta el formulario. |
| Django + DRF | 6.1.2 / 3.18.3 | Aplicación bajo prueba y API `/api/register/`. |
| SQLite | `db.sqlite3` | Verificación de usuarios creados. |

Estas versiones corresponden al entorno en el que se ejecutaron las pruebas; no deben actualizarse como parte de esta documentación.

### 12.3. Requisitos previos

- Entorno virtual y dependencias instaladas según la sección 3.
- Servidor de Django activo según la sección 5.
- Google Chrome instalado. Selenium Manager descarga automáticamente Chrome for Testing y `chromedriver` si no los encuentra en el sistema; en este entorno se usaron los archivos de `%USERPROFILE%\.cache\selenium`.
- Permisos de escritura sobre `db.sqlite3`, porque los casos aceptados crean cuentas reales. No ejecute la batería contra una base de datos de producción (sección 4).

### 12.4. Instalación de dependencias

La instalación se describe en la sección 3. `selenium` ya figura en `requirements.txt`, por lo que no es necesario añadir dependencias nuevas.

### 12.5. Activación del entorno virtual

La activación se describe en la sección 3. El comando `.\venv\Scripts\Activate.ps1` activa el entorno; si se ejecuta sin más argumentos en una terminal interactiva, abre el intérprete de Python, por lo que **no** es el comando que inicia las pruebas. Para ejecutar la batería se invoca el módulo con el intérprete del entorno:

```powershell
.\venv\Scripts\python.exe -m selenium_tests.test_selenium
```

Las variantes para casos individuales están en la sección 12.12.

### 12.6. Configuración de Google Chrome y Selenium

`selenium_tests/configuracion.py` define:

- `URL_REGISTRO`: `http://127.0.0.1:8000/registro/` por defecto.
- `TIEMPO_ESPERA`: 10 segundos para las esperas explícitas.
- `crear_navegador()`: instancia Chrome con `--start-maximized` y maximiza la ventana.

Variables de entorno opcionales:

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `SELENIUM_URL_BASE` | `http://127.0.0.1:8000` | Cambiar el servidor objetivo. |
| `SELENIUM_ESPERA` | `10` | Segundos máximos de espera. |
| `SELENIUM_HEADLESS` | sin valor | Si es `1`, Chrome se ejecuta sin ventana visible. |

Ejemplo de ejecución en modo headless:

```powershell
$env:SELENIUM_HEADLESS = '1'
.\venv\Scripts\python.exe -m selenium_tests.test_selenium
```

La sincronización se realiza con `WebDriverWait` y condiciones esperadas de Selenium. **No se utiliza `time.sleep()`** ni pausas fijas para esperar las respuestas del formulario.

### 12.7. Cómo iniciar el servidor Django

El arranque del servidor se describe en la sección 5:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Deje esa terminal abierta y ejecute la batería en otra terminal. `migrate` sólo es necesario si la base de datos aún no está aplicada (sección 4).

### 12.8. Cómo preparar la base de datos para las pruebas

```powershell
.\venv\Scripts\python.exe -m selenium_tests.preparar_base
```

Ese comando garantiza la existencia de `jose@gmail.com` sin duplicarlo y sin tocar otras cuentas; es requisito de CP-12 y CP-24. Si el correo ya existía, se conserva sin cambios y no se marca como generado por Selenium, por lo que la limpieza no lo eliminará. Los detalles y el procedimiento de limpieza están en la sección 10.

### 12.9. Estructura de la carpeta `selenium_tests`

```text
selenium_tests/
├── __init__.py
├── configuracion.py
├── funciones.py
├── datos_prueba.py
├── casos_prueba.py
├── test_selenium.py
├── preparar_base.py
├── limpiar_datos_prueba.py
├── .cuenta_previa_generada.txt  # sólo si el script creó la cuenta; no se versiona
└── resultados/                  # se crea automáticamente; no se versiona
    └── ejecucion_sel_....txt
```

### 12.10. Descripción de cada archivo

| Archivo | Responsabilidad |
| --- | --- |
| `__init__.py` | Marca el paquete Python. |
| `configuracion.py` | URL del formulario, tiempo de espera, rutas de informes y del marcador de cuenta previa, y creación del navegador. |
| `funciones.py` | Abrir el formulario, completar y enviar campos, esperar el mensaje, analizar los errores por campo y consultar el ORM de Django. |
| `datos_prueba.py` | Los 27 casos con sus entradas y resultados esperados; generador del sufijo único de cada ejecución. |
| `casos_prueba.py` | Ejecutar y evaluar cada caso, mostrar los informes en consola y guardar el archivo de resultados. |
| `test_selenium.py` | Punto de entrada: selecciona los casos, administra el navegador y muestra el resumen. |
| `preparar_base.py` | Crea de forma idempotente la cuenta previa de CP-12 y CP-24 y marca su identificador cuando la crea. |
| `limpiar_datos_prueba.py` | Simulación por defecto; con `--confirmar` elimina sólo los correos generados por la batería y la cuenta previa marcada. |

### 12.11. Cómo ejecutar todos los casos de prueba

Con el servidor activo y la cuenta previa preparada:

```powershell
.\venv\Scripts\python.exe -m selenium_tests.test_selenium
```

También puede escribirse `TODOS` de forma explícita:

```powershell
.\venv\Scripts\python.exe -m selenium_tests.test_selenium TODOS
```

### 12.12. Cómo ejecutar un caso individual

Se indican los identificadores deseados, separados por espacios:

```powershell
.\venv\Scripts\python.exe -m selenium_tests.test_selenium CP-02
.\venv\Scripts\python.exe -m selenium_tests.test_selenium CP-12 CP-24
```

Los identificadores no distinguen mayúsculas. Si se escribe un caso inexistente, el programa muestra un aviso y termina con código `2`.

### 12.13. Cómo interpretar los resultados

Para cada caso se muestra un bloque con los datos ingresados (la contraseña siempre aparece como `********` y, como máximo, su longitud), el resultado esperado, el obtenido y el estado:

- **APROBADO**: el mensaje, los campos con error y el estado de la base de datos coinciden con la planilla.
- **RECHAZADO**: la aplicación respondió de forma distinta a lo esperado. El bloque indica la diferencia concreta.
- **ERROR DE EJECUCIÓN**: un problema técnico (servidor caído, Chrome no disponible, tiempo de espera agotado, etc.) impidió completar el caso. No se confunde con un error de validación de Django.

Al final se imprime el resumen con el total, los aprobados, los rechazados, los errores de ejecución y el porcentaje de aprobación. El código de salida es `0` si todos los casos se aprobaron, `1` si hubo rechazos o errores y `2` si falló la configuración inicial.

Cada ejecución guarda además un informe de texto en `selenium_tests/resultados/ejecucion_<sufijo>.txt`, con el mismo detalle y contraseñas enmascaradas. Esa carpeta está excluida de Git para no versionar historiales locales.

### 12.14. Solución de problemas frecuentes

| Síntoma | Causa probable | Acción |
| --- | --- | --- |
| `No se pudo iniciar Chrome` | Chrome no instalado o sin permisos. | Instalar Google Chrome o verificar `%USERPROFILE%\.cache\selenium`. |
| `Timeout` esperando el mensaje | El servidor no responde o la URL es incorrecta. | Confirmar `runserver` y, si hace falta, definir `SELENIUM_URL_BASE`. |
| CP-12/CP-24 rechazados por "correo no registrado" | Falta la cuenta previa. | Ejecutar `python -m selenium_tests.preparar_base`. |
| Correo duplicado en un caso aceptado | Se reutilizó el sufijo de una pasada anterior. | No editar `datos_prueba.py`; cada ejecución genera un sufijo nuevo. |
| `manage.py test` detecta un error en `selenium_tests` | Se ejecutó el módulo como script en vez de importarlo. | Usar `.\venv\Scripts\python.exe -m selenium_tests.test_selenium`. |
| El puerto 8000 está ocupado | Otro servidor Django activo. | Cerrarlo o indicar otra URL con `SELENIUM_URL_BASE`. |
| La ventana de Chrome molesta en el escritorio | Ejecución visible. | Definir `$env:SELENIUM_HEADLESS = '1'`. |

### 12.15. Resultados reales de la ejecución

La ejecución completa más reciente se realizó el **19 de noviembre de 2026** (00:17, hora local) contra `http://127.0.0.1:8000/registro/`, con Chrome en modo headless y la cuenta previa ya preparada:

```text
Total de casos: 27
Aprobados: 27
Rechazados: 0
Errores de ejecución: 0
Porcentaje de aprobación: 100 %
```

El informe correspondiente es `selenium_tests/resultados/ejecucion_sel_20261119001725_f64c12.txt`. Durante esa pasada se crearon los 8 usuarios de los casos aceptados; sus correos llevan el sufijo `sel_20261119001725_f64c12`. La cuenta `jose@gmail.com` no se duplicó.

En la misma revisión se ejecutaron también un caso individual (`CP-02`, 1/1 aprobado; informe `ejecucion_sel_20261119001703_14268c.txt`) y dos casos seleccionados (`CP-12 CP-24`, 2/2 aprobados; informe `ejecucion_sel_20261119001715_9b1c5d.txt`). Los informes se generaron correctamente, no contienen contraseñas y el navegador se cerró al finalizar cada ejecución.

En una pasada anterior se obtuvieron 25 aprobados y 2 rechazados: el problema estaba en la evaluación del runner, que consideraba "usuario creado" a la cuenta previa necesaria para CP-12 y CP-24. Se corrigió esa comprobación (comparando identificadores de usuario) y se volvió a ejecutar la batería completa, obteniendo el resultado mostrado arriba. No se modificaron las reglas de negocio de la aplicación.

La suite de Django terminó con **54 pruebas, OK**, sin alterar `db.sqlite3`. La revisión final comprobó además `manage.py check` (sin problemas) y `manage.py makemigrations --check --dry-run` (`No changes detected`). El modo simulación de limpieza no eliminó ninguna cuenta y conservó `jose@gmail.com` al no existir marcador de creación; **no se ejecutó la eliminación real con `--confirmar`**.
