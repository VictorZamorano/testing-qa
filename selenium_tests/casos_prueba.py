"""Ejecución, evaluación y presentación de cada caso del CU-01."""

from datetime import datetime

from selenium_tests import configuracion, datos_prueba, funciones

SEPARADOR = "=" * 40


def _evaluar(caso, respuesta, usuario_antes, usuario_despues):
    """Compara la respuesta de la aplicación con lo esperado por la planilla."""
    problemas = []
    es_duplicado = caso["correo"] == datos_prueba.CORREO_PREVIO

    if usuario_antes is not None and not es_duplicado:
        problemas.append("el correo ya estaba registrado antes del caso")

    if caso["debe_aceptarse"]:
        if respuesta["tipo"] != "exito":
            problemas.append("no se mostró el mensaje de éxito")
        elif respuesta["texto"] != datos_prueba.MENSAJE_EXITO:
            problemas.append(
                f"mensaje de éxito inesperado: {respuesta['texto']!r}"
            )

        if (
            usuario_despues is None
            or usuario_antes is not None
            and usuario_despues.pk == usuario_antes.pk
        ):
            problemas.append("no se creó un usuario nuevo en la base de datos")
        else:
            if usuario_despues.nombre_completo != caso["nombre"]:
                problemas.append(
                    f"nombre guardado incorrecto: {usuario_despues.nombre_completo!r}"
                )
            if usuario_despues.rol != "usuario":
                problemas.append(f"rol incorrecto: {usuario_despues.rol!r}")
    else:
        if respuesta["tipo"] != "error":
            problemas.append("no se mostró el mensaje de error")
        else:
            errores = funciones.parsear_errores(respuesta["texto"])
            if not errores:
                problemas.append("el mensaje de error no identifica ningún campo")
            for campo in caso["campos_error"]:
                if campo not in errores:
                    problemas.append(f"falta el error correspondiente a {campo}")
            for campo in caso["campos_sin_error"]:
                if campo in errores:
                    problemas.append(f"se informó un error inesperado en {campo}")

        if es_duplicado:
            if (
                usuario_antes is None
                or usuario_despues is None
                or usuario_despues.pk != usuario_antes.pk
            ):
                problemas.append("no se conservó la cuenta previa sin duplicarla")
        elif usuario_despues is not None:
            problemas.append("se creó un usuario con datos inválidos")

    return problemas


def _resultado(caso, correo, estado, esperado, obtenido, detalle):
    contrasena = caso["password"]
    return {
        "id": caso["id"],
        "titulo": caso["titulo"],
        "estado": estado,
        "esperado": esperado,
        "obtenido": obtenido,
        "detalle": detalle,
        "datos": {
            "nombre": caso["nombre"],
            "correo": correo,
            "contrasena": "********",
            "longitud": len(contrasena),
        },
    }


def ejecutar_caso(navegador, caso, sufijo):
    """Ejecuta un caso en el navegador y devuelve su resultado."""
    correo = caso["correo"]
    if caso["debe_aceptarse"]:
        correo = datos_prueba.agregar_sufijo(correo, sufijo)

    if caso["debe_aceptarse"]:
        esperado = datos_prueba.MENSAJE_EXITO
    else:
        esperado = "Rechazo del registro; errores en: " + ", ".join(
            caso["campos_error"]
        )

    usuario_antes = funciones.obtener_usuario(correo)
    funciones.completar_formulario(
        navegador, caso["nombre"], correo, caso["password"]
    )
    funciones.enviar_formulario(navegador)
    respuesta = funciones.esperar_respuesta(navegador)
    usuario_despues = funciones.obtener_usuario(correo)

    problemas = _evaluar(caso, respuesta, usuario_antes, usuario_despues)
    estado = "APROBADO" if not problemas else "RECHAZADO"

    if caso["correo"] == datos_prueba.CORREO_PREVIO:
        conservada = (
            usuario_antes is not None
            and usuario_despues is not None
            and usuario_despues.pk == usuario_antes.pk
        )
        detalle = (
            "Cuenta previa conservada sin duplicados: "
            f"{'sí' if conservada else 'no'}."
        )
    else:
        creado = "sí" if usuario_despues is not None else "no"
        detalle = f"Usuario en la BD después del caso: {creado}."
    if problemas:
        detalle += " " + "; ".join(problemas) + "."

    return _resultado(
        caso, correo, estado, esperado, respuesta["texto"], detalle
    )


def resultado_error(caso, error, sufijo):
    """Representa un fallo técnico que impidió completar el caso."""
    correo = caso["correo"]
    if caso["debe_aceptarse"]:
        correo = datos_prueba.agregar_sufijo(correo, sufijo)
    return _resultado(
        caso,
        correo,
        "ERROR DE EJECUCIÓN",
        "No aplica: falló la ejecución del caso.",
        f"{type(error).__name__}: {error}",
        "No fue posible completar la prueba; revise el servidor y el navegador.",
    )


def _texto_resultado(resultado):
    datos = resultado["datos"]
    contrasena = (
        f"{datos['contrasena']} (longitud: {datos['longitud']})"
        if datos["longitud"]
        else "******** (vacía)"
    )
    lineas = [
        SEPARADOR,
        f"{resultado['id']}: {resultado['titulo'].upper()}",
        SEPARADOR,
        "",
        "Datos ingresados:",
        f"Nombre: {datos['nombre'] or '(vacío)'}",
        f"Correo: {datos['correo'] or '(vacío)'}",
        f"Contraseña: {contrasena}",
        "",
        f"Resultado esperado: {resultado['esperado']}",
        f"Resultado obtenido: {resultado['obtenido']}",
        "",
        f"Detalle: {resultado['detalle']}",
        "",
        f"Estado: {resultado['estado']}",
        SEPARADOR,
    ]
    return "\n".join(lineas)


def mostrar_resultado(resultado):
    """Muestra en consola el informe de un caso."""
    print("\n" + _texto_resultado(resultado))


def _texto_resumen(resultados):
    aprobados = sum(r["estado"] == "APROBADO" for r in resultados)
    rechazados = sum(r["estado"] == "RECHAZADO" for r in resultados)
    errores = sum(r["estado"] == "ERROR DE EJECUCIÓN" for r in resultados)
    total = len(resultados)
    porcentaje = round(aprobados / total * 100) if total else 0

    return "\n".join(
        [
            "",
            SEPARADOR,
            "RESUMEN DE PRUEBAS",
            SEPARADOR,
            "",
            f"Total de casos: {total}",
            f"Aprobados: {aprobados}",
            f"Rechazados: {rechazados}",
            f"Errores de ejecución: {errores}",
            "",
            f"Porcentaje de aprobación: {porcentaje} %",
            "",
            SEPARADOR,
        ]
    )


def mostrar_resumen(resultados):
    """Muestra en consola el resumen general de la ejecución."""
    print(_texto_resumen(resultados))


def guardar_informe(resultados, sufijo):
    """Guarda el historial de ejecución sin incluir contraseñas reales."""
    configuracion.RAIZ_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = configuracion.RAIZ_RESULTADOS / f"ejecucion_{sufijo}.txt"
    encabezado = "\n".join(
        [
            "INFORME DE EJECUCIÓN - CU-01 REGISTRO DE USUARIOS",
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"URL del formulario: {configuracion.URL_REGISTRO}",
            f"Identificador de ejecución: {sufijo}",
            "",
        ]
    )
    bloques = "\n\n".join(_texto_resultado(r) for r in resultados)
    ruta.write_text(
        encabezado + bloques + "\n\n" + _texto_resumen(resultados) + "\n",
        encoding="utf-8",
    )
    return ruta
