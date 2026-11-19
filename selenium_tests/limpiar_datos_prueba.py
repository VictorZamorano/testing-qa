"""Limpieza explícita y limitada de las cuentas creadas por la batería Selenium.

Sin argumentos sólo simula y muestra qué cuentas se eliminarían y cuáles se
conservan. La eliminación real exige la opción ``--confirmar``.

La cuenta previa de CP-12 y CP-24 sólo se elimina si existe un marcador
escrito por ``preparar_base.py`` con el identificador de la cuenta que él
creó. Si el correo ya existía antes, no hay marcador y se conserva.
"""

import re
import sys

from django.contrib.auth import get_user_model

from selenium_tests import configuracion, datos_prueba, funciones

PATRON_CORREO_GENERADO = re.compile(
    r"jose\.cp\d+\+sel_[0-9]{14}_[0-9a-f]{6}@gmail\.com", re.IGNORECASE
)


def _id_previa_generada():
    """Devuelve el id de la cuenta previa creada por el script, o None."""
    try:
        return int(
            configuracion.ARCHIVO_MARCA_PREVIA.read_text(encoding="utf-8").strip()
        )
    except (OSError, ValueError):
        return None


def _es_generada(usuario):
    correo = (usuario.email or "").lower()
    return (
        usuario.rol == "usuario"
        and usuario.nombre_completo == datos_prueba.NOMBRE_COMPLETO
        and PATRON_CORREO_GENERADO.fullmatch(correo) is not None
    )


def _es_previa_generada(usuario, id_previa):
    return (
        id_previa is not None
        and usuario.pk == id_previa
        and usuario.rol == "usuario"
        and usuario.username == datos_prueba.USUARIO_PREVIO
        and (usuario.email or "").lower() == datos_prueba.CORREO_PREVIO.lower()
    )


def _seleccionar(usuarios, id_previa):
    return [
        usuario
        for usuario in usuarios
        if _es_generada(usuario) or _es_previa_generada(usuario, id_previa)
    ]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    confirmar = argv == ["--confirmar"]
    if argv and not confirmar:
        print("Uso: python -m selenium_tests.limpiar_datos_prueba [--confirmar]")
        return 2

    funciones.configurar_django()
    usuarios = list(get_user_model().objects.all())
    id_previa = _id_previa_generada()
    eliminar = _seleccionar(usuarios, id_previa)
    ids_eliminar = {usuario.pk for usuario in eliminar}
    conservar = [usuario for usuario in usuarios if usuario.pk not in ids_eliminar]

    print(f"Marcador de cuenta previa: {id_previa if id_previa else 'ausente'}")
    print("\nCuentas que se eliminarían:")
    if eliminar:
        for usuario in eliminar:
            print(
                f"  id={usuario.id} usuario={usuario.username} "
                f"correo={usuario.email}"
            )
    else:
        print("  (ninguna)")

    print("\nCuentas que se conservan:")
    for usuario in conservar:
        detalle = ""
        if (usuario.email or "").lower() == datos_prueba.CORREO_PREVIO.lower():
            detalle = " (cuenta previa; no marcada como generada por Selenium)"
        print(
            f"  id={usuario.id} usuario={usuario.username} "
            f"correo={usuario.email}{detalle}"
        )
    administradores = sum(u.rol == "administrador" for u in conservar)
    print(
        f"  Total de cuentas conservadas: {len(conservar)} "
        f"(administradores: {administradores})."
    )

    if not confirmar:
        print("\nModo simulación: no se eliminó ninguna cuenta.")
        print("Para eliminarlas, añada la opción --confirmar.")
        return 0

    for usuario in eliminar:
        usuario.delete()
    if id_previa is not None and id_previa in ids_eliminar:
        configuracion.ARCHIVO_MARCA_PREVIA.unlink(missing_ok=True)
    print(f"\nSe eliminaron {len(eliminar)} cuentas de prueba.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
