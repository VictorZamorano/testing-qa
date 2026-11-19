"""Punto de entrada de la batería Selenium del CU-01.

Ejecución completa:   python -m selenium_tests.test_selenium
Caso individual:      python -m selenium_tests.test_selenium CP-02
Varios casos:         python -m selenium_tests.test_selenium CP-12 CP-24
"""

import sys

from selenium_tests import casos_prueba, configuracion, datos_prueba, funciones


def _ids_solicitados(argumentos, casos):
    """Valida los identificadores de caso indicados en la línea de comandos."""
    ids_validos = {caso["id"] for caso in casos}
    if not argumentos or argumentos[0].upper() == "TODOS":
        return [caso["id"] for caso in casos]

    ids = []
    for argumento in argumentos:
        id_caso = argumento.upper()
        if id_caso not in ids_validos:
            raise ValueError(
                f"Caso desconocido: {argumento}. Use CP-01 ... CP-27 o TODOS."
            )
        if id_caso not in ids:
            ids.append(id_caso)
    return ids


def main(argv=None):
    """Ejecuta los casos seleccionados y devuelve un código de salida."""
    argv = sys.argv[1:] if argv is None else argv
    funciones.configurar_django()
    casos = datos_prueba.construir_casos()

    try:
        ids = _ids_solicitados(argv, casos)
    except ValueError as error:
        print(error)
        return 2

    seleccionados = [caso for caso in casos if caso["id"] in ids]
    if any(
        caso["correo"] == datos_prueba.CORREO_PREVIO for caso in seleccionados
    ) and funciones.obtener_usuario(datos_prueba.CORREO_PREVIO) is None:
        print(
            "AVISO: CP-12/CP-24 necesitan la cuenta previa. Ejecute primero:\n"
            "  python -m selenium_tests.preparar_base"
        )

    sufijo = datos_prueba.generar_sufijo()
    print(f"Ejecución {sufijo}")
    print(f"Formulario: {configuracion.URL_REGISTRO}")
    print(f"Casos seleccionados: {len(seleccionados)}")

    try:
        navegador = configuracion.crear_navegador()
    except Exception as error:
        print(f"No se pudo iniciar Chrome: {type(error).__name__}: {error}")
        return 2

    resultados = []
    try:
        for caso in seleccionados:
            try:
                resultado = casos_prueba.ejecutar_caso(navegador, caso, sufijo)
            except Exception as error:
                resultado = casos_prueba.resultado_error(caso, error, sufijo)
            casos_prueba.mostrar_resultado(resultado)
            resultados.append(resultado)
    finally:
        navegador.quit()

    casos_prueba.mostrar_resumen(resultados)
    ruta = casos_prueba.guardar_informe(resultados, sufijo)
    print(f"Informe guardado en: {ruta}")

    if any(r["estado"] != "APROBADO" for r in resultados):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
