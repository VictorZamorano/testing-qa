"""Datos de entrada y resultados esperados de los 27 casos del CU-01.

Los valores (nombres, correos y longitudes de contraseña) proceden de la
planilla implementada originalmente en ``tareas/tests_cu01.py``. Los correos
de los casos aceptados reciben un sufijo único por ejecución para no colisionar
con registros de pasadas anteriores.
"""

from datetime import datetime
from uuid import uuid4

NOMBRE_COMPLETO = "José Pérez"
CORREO_PREVIO = "jose@gmail.com"
USUARIO_PREVIO = "cuenta_previa_cu01"
MENSAJE_EXITO = "Registro exitoso."


def password_de(longitud):
    """Reproduce la contraseña de prueba de la planilla original."""
    patron = "Ab1!" * ((longitud // 4) + 1)
    return patron[:longitud]


PASSWORD_VALIDO = password_de(12)


def generar_sufijo():
    """Devuelve un identificador único para la ejecución actual."""
    return f"sel_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}"


def agregar_sufijo(correo, sufijo):
    """Añade el sufijo de ejecución antes de la @ del correo."""
    local, dominio = correo.rsplit("@", 1)
    return f"{local}+{sufijo}@{dominio}"


def _caso(
    id_caso,
    titulo,
    tecnica,
    nombre,
    correo,
    password,
    aceptado,
    campos_error=(),
    campos_sin_error=(),
):
    return {
        "id": id_caso,
        "titulo": titulo,
        "tecnica": tecnica,
        "nombre": nombre,
        "correo": correo,
        "password": password,
        "debe_aceptarse": aceptado,
        "campos_error": campos_error,
        "campos_sin_error": campos_sin_error,
    }


PARTICION = "Partición de equivalencia"
LIMITE = "Valor límite"
CAUSA_EFECTO = "Causa-efecto"


def construir_casos():
    """Devuelve los 27 casos en el orden de la planilla."""
    return [
        _caso("CP-01", "Nombre vacío", PARTICION, "", "jose.cp01@gmail.com", PASSWORD_VALIDO, False, ("username",)),
        _caso("CP-02", "Registro válido", PARTICION, NOMBRE_COMPLETO, "jose.cp02@gmail.com", PASSWORD_VALIDO, True),
        _caso("CP-03", "Correo vacío", PARTICION, NOMBRE_COMPLETO, "", PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-04", "Correo válido", PARTICION, NOMBRE_COMPLETO, "jose.cp04@gmail.com", PASSWORD_VALIDO, True),
        _caso("CP-05", "Correo incompleto", PARTICION, NOMBRE_COMPLETO, "jose@gmail", PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-06", "Correo sin dominio", PARTICION, NOMBRE_COMPLETO, "jose", PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-07", "Correo sin arroba", PARTICION, NOMBRE_COMPLETO, "jose.gmail.com", PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-08", "Contraseña vacía", PARTICION, NOMBRE_COMPLETO, "jose.cp08@gmail.com", "", False, ("password",)),
        _caso("CP-09", "Contraseña inferior al mínimo", PARTICION, NOMBRE_COMPLETO, "jose.cp09@gmail.com", password_de(5), False, ("password",)),
        _caso("CP-10", "Contraseña en el mínimo", PARTICION, NOMBRE_COMPLETO, "jose.cp10@gmail.com", password_de(8), True),
        _caso("CP-11", "Contraseña superior al máximo", PARTICION, NOMBRE_COMPLETO, "jose.cp11@gmail.com", password_de(23), False, ("password",)),
        _caso("CP-12", "Correo duplicado", PARTICION, NOMBRE_COMPLETO, CORREO_PREVIO, PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-13", "Contraseña de 7 caracteres", LIMITE, NOMBRE_COMPLETO, "jose.cp13@gmail.com", password_de(7), False, ("password",)),
        _caso("CP-14", "Contraseña de 8 caracteres", LIMITE, NOMBRE_COMPLETO, "jose.cp14@gmail.com", password_de(8), True),
        _caso("CP-15", "Contraseña de 9 caracteres", LIMITE, NOMBRE_COMPLETO, "jose.cp15@gmail.com", password_de(9), True),
        _caso("CP-16", "Contraseña de 19 caracteres", LIMITE, NOMBRE_COMPLETO, "jose.cp16@gmail.com", password_de(19), True),
        _caso("CP-17", "Contraseña de 20 caracteres", LIMITE, NOMBRE_COMPLETO, "jose.cp17@gmail.com", password_de(20), True),
        _caso("CP-18", "Contraseña de 21 caracteres", LIMITE, NOMBRE_COMPLETO, "jose.cp18@gmail.com", password_de(21), False, ("password",)),
        _caso("CP-19", "Todos los campos válidos y correo disponible", CAUSA_EFECTO, NOMBRE_COMPLETO, "jose.cp19@gmail.com", PASSWORD_VALIDO, True),
        _caso("CP-20", "Nombre vacío y resto válido", CAUSA_EFECTO, "", "jose.cp20@gmail.com", PASSWORD_VALIDO, False, ("username",), ("email", "password")),
        _caso("CP-21", "Correo jose@gmail y resto válido", CAUSA_EFECTO, NOMBRE_COMPLETO, "jose@gmail", PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-22", "Contraseña de 5 caracteres y resto válido", CAUSA_EFECTO, NOMBRE_COMPLETO, "jose.cp22@gmail.com", password_de(5), False, ("password",)),
        _caso("CP-23", "Nombre vacío y contraseña de 5 caracteres", CAUSA_EFECTO, "", "jose.cp23@gmail.com", password_de(5), False, ("username", "password"), ("email",)),
        _caso("CP-24", "Correo jose@gmail.com duplicado", CAUSA_EFECTO, NOMBRE_COMPLETO, CORREO_PREVIO, PASSWORD_VALIDO, False, ("email",)),
        _caso("CP-25", "Nombre vacío y correo inválido", CAUSA_EFECTO, "", "jose@gmail", PASSWORD_VALIDO, False, ("username", "email"), ("password",)),
        _caso("CP-26", "Nombre, correo y contraseña inválidos", CAUSA_EFECTO, "", "mal", "123", False, ("username", "email", "password")),
        _caso("CP-27", "Correo inválido y contraseña inválida", CAUSA_EFECTO, NOMBRE_COMPLETO, "jose@gmail", password_de(5), False, ("email", "password"), ("username",)),
    ]
