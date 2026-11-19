"""Crea, una sola vez y de forma controlada, la cuenta previa de CP-12 y CP-24.

Si la cuenta ya existe se conserva sin cambios y no se escribe ningún marcador;
así la limpieza puede distinguirla de una cuenta creada por este script.
"""

from django.contrib.auth import get_user_model

from selenium_tests import configuracion, datos_prueba, funciones


def main():
    funciones.configurar_django()
    usuarios = get_user_model().objects
    correo = datos_prueba.CORREO_PREVIO

    existente = usuarios.filter(email__iexact=correo).first()
    if existente is not None:
        print(
            f"La cuenta previa ya existe (id={existente.id}, "
            f"usuario={existente.username}). No se realizó ningún cambio."
        )
        return 0

    nombre_usuario = datos_prueba.USUARIO_PREVIO
    contador = 2
    while usuarios.filter(username=nombre_usuario).exists():
        nombre_usuario = f"{datos_prueba.USUARIO_PREVIO}_{contador}"
        contador += 1

    creada = usuarios.create_user(
        username=nombre_usuario,
        email=correo,
        password=datos_prueba.PASSWORD_VALIDO,
        rol="usuario",
        is_active=True,
    )
    configuracion.ARCHIVO_MARCA_PREVIA.write_text(
        str(creada.pk), encoding="utf-8"
    )
    print(f"Cuenta previa creada: {nombre_usuario} / {correo}")
    print("Contraseña: ******** (no se muestra por seguridad).")
    print("Quedó marcada como generada por Selenium para permitir su limpieza.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
