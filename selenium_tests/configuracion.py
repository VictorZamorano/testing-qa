"""Configuración compartida de la batería Selenium del CU-01."""

import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL_BASE = os.environ.get("SELENIUM_URL_BASE", "http://127.0.0.1:8000").rstrip("/")
URL_REGISTRO = f"{URL_BASE}/registro/"
TIEMPO_ESPERA = int(os.environ.get("SELENIUM_ESPERA", "10"))
RAIZ_RESULTADOS = Path(__file__).resolve().parent / "resultados"
ARCHIVO_MARCA_PREVIA = Path(__file__).resolve().parent / ".cuenta_previa_generada.txt"


def crear_navegador():
    """Crea una instancia de Chrome para ejecutar los casos de prueba."""
    opciones = Options()
    opciones.add_argument("--start-maximized")

    if os.environ.get("SELENIUM_HEADLESS") == "1":
        opciones.add_argument("--headless=new")

    navegador = webdriver.Chrome(options=opciones)

    navegador.maximize_window()

    return navegador
