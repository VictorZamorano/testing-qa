
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

URL_REGISTRO = "http://127.0.0.1:8000/registro/"


def crear_navegador():
    opciones = Options()
    opciones.add_argument("--start-maximized")

    navegador = webdriver.Chrome(options=opciones)

    navegador.maximize_window()

    return navegador
