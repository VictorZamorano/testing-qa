
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium_tests.configuracion import URL_REGISTRO, crear_navegador

navegador = crear_navegador()

try:
    # 1. Abrir el formulario
    navegador.get(URL_REGISTRO)

    # 2. Localizar los campos
    nombre = navegador.find_element(By.ID, "username")
    correo = navegador.find_element(By.ID, "email")
    password = navegador.find_element(By.ID, "password")

    # 3. Introducir los datos de prueba
    nombre.send_keys("José Pérez")

    # Correo diferente en cada ejecución para evitar duplicados
    correo_prueba = f"selenium_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
    correo.send_keys(correo_prueba)

    password.send_keys("Test12345")

    # 4. Enviar el formulario
    navegador.find_element(
        By.CSS_SELECTOR, "button[type='submit']"
    ).click()

    # 5. Esperar a que aparezca el mensaje de éxito
    mensaje_exito = WebDriverWait(navegador, 10).until(
        EC.visibility_of_element_located((By.ID, "success-message"))
    )

    # 6. Comprobar el resultado
    mensaje_error = navegador.find_element(By.ID, "error-message")

    assert mensaje_exito.is_displayed(), "No apareció el mensaje de éxito."
    assert not mensaje_error.is_displayed(), "Se mostró un mensaje de error."

    print("\n========================================")
    print("CP-02: REGISTRO VÁLIDO")
    print("========================================")

    print("Datos ingresados:")
    print("Nombre:", "José Pérez")
    print("Correo:", correo_prueba)
    print("Contraseña:", "********")

    print("\nResultado esperado: Registro exitoso.")
    print("Resultado obtenido:", mensaje_exito.text)
    print("Estado: APROBADO")

    print("========================================")

finally:
    navegador.quit()
