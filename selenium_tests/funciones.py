"""Funciones reutilizables para interactuar con el formulario y la base de datos."""

import os
import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium_tests.configuracion import TIEMPO_ESPERA, URL_REGISTRO

CAMPOS_VALIDACION = ("username", "email", "password", "non_field_errors")
_django_configurado = False


def configurar_django():
    """Inicializa Django para poder consultar la BD con el ORM."""
    global _django_configurado
    if _django_configurado:
        return
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestor_tareas.settings")
    import django

    django.setup()
    _django_configurado = True


def abrir_formulario(navegador):
    """Carga el formulario y espera a que sus campos estén visibles."""
    navegador.get(URL_REGISTRO)
    espera = WebDriverWait(navegador, TIEMPO_ESPERA)
    espera.until(EC.visibility_of_element_located((By.ID, "register-form")))
    return (
        espera.until(EC.visibility_of_element_located((By.ID, "username"))),
        espera.until(EC.visibility_of_element_located((By.ID, "email"))),
        espera.until(EC.visibility_of_element_located((By.ID, "password"))),
    )


def completar_formulario(navegador, nombre, correo, contrasena):
    """Escribe los datos en los tres campos; los valores vacíos quedan vacíos."""
    campo_nombre, campo_correo, campo_contrasena = abrir_formulario(navegador)
    for campo, valor in zip(
        (campo_nombre, campo_correo, campo_contrasena),
        (nombre, correo, contrasena),
    ):
        campo.clear()
        if valor:
            campo.send_keys(valor)


def enviar_formulario(navegador):
    """Pulsa el botón de envío del formulario."""
    boton = WebDriverWait(navegador, TIEMPO_ESPERA).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    boton.click()


def _leer_mensaje_visible(navegador):
    """Condición esperada propia: devuelve el mensaje de éxito o error visible."""
    for id_mensaje, tipo in (("success-message", "exito"), ("error-message", "error")):
        try:
            elemento = navegador.find_element(By.ID, id_mensaje)
            if elemento.is_displayed() and elemento.text.strip():
                return {"tipo": tipo, "texto": elemento.text.strip()}
        except StaleElementReferenceException:
            continue
    return False


def esperar_respuesta(navegador):
    """Espera a que la aplicación muestre su mensaje de éxito o de error."""
    return WebDriverWait(navegador, TIEMPO_ESPERA).until(_leer_mensaje_visible)


def parsear_errores(texto):
    """Convierte el texto 'campo: mensaje' del formulario en un diccionario."""
    errores = {}
    for linea in texto.splitlines():
        coincidencia = re.match(r"^\s*([A-Za-z_]+)\s*:\s*(.*)$", linea)
        if coincidencia and coincidencia.group(1) in CAMPOS_VALIDACION:
            errores[coincidencia.group(1)] = coincidencia.group(2).strip()
    return errores


def obtener_usuario(correo):
    """Busca un usuario por correo sin distinguir mayúsculas; None si no existe."""
    from django.contrib.auth import get_user_model

    return get_user_model().objects.filter(email__iexact=correo).first()
