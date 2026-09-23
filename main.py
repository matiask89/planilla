from datetime import datetime
import time
import os
import urllib.request
import urllib.parse
import requests
from playwright.sync_api import sync_playwright

def iniciar_sesion_y_automatizar():
    # Iniciamos Playwright
    with sync_playwright() as p:
        # Lanzamos el navegador (cambia headless=True si quieres que sea invisible)
        # slow_mo=500 agrega una pausa de medio segundo entre acciones para que la web no sospeche
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        try:
            # 1. Navegar a la página web
            print("Abriendo la página web...")
            page.goto("https://empleadospublicos.larioja.gob.ar/recibos/web/login") # URL real aquí

            # 2. Rellenar el formulario de inicio de sesión
            print("Introduciendo credenciales...")
            # Reemplaza 'input[type="email"]' por el selector real de la web
            page.fill('//*[@id="username"]', "27364365670")
            page.fill('//*[@id="password"]', "mery123")

            # 3. Hacer clic en el botón de ingresar
            print("Haciendo clic en el botón de iniciar sesión...")
            # Reemplaza 'button[type="submit"]' por el selector real del botón
            page.click('//*[@id="_submit"]')

            # 4. Esperar a que la página cargue tras el inicio de sesión
            # Puedes esperar a que cambie la URL o a que aparezca un elemento del menú
            page.wait_for_load_state("networkidle") 
            print("¡Inicio de sesión completado con éxito!")

           # 1. Definimos el elemento usando su XPath, ID o CSS
            elemento = page.locator('//a[@href="/recibos/web/asistencia/"]')

            # 2. Verificamos si existe en la página
            if elemento.count() > 0:
                print("El elemento X existe. Realizando acción A...")
                # Aquí pones el código que quieres que se ejecute si existe
                elemento.click()

                   # 1. Seleccionamos las opciones en el formulario
        
                    # 1. Seleccionamos las opciones en el formulario
            page.locator('//*[@id="empleadosbundle_asistencia_organismo"]').select_option("UNIDAD DE CONTROL INTERNO - VIALIDAD")
            page.locator('//*[@id="empleadosbundle_asistencia_isEntrada"]').select_option("0")

            carpeta_descargas_windows = os.path.join(os.path.expanduser("~"), "Downloads")
        
            # Obtenemos la fecha actual en formato AÑO-MES-DIA (ej: 2026-07-16)
            fecha_hoy = datetime.now().strftime("%d-%m-%Y")
            
            # Creamos el nombre del archivo dinámico con la fecha
            nombre_archivo = f"planilla_asistencia_{fecha_hoy}.pdf"
            ruta_final = os.path.join(carpeta_descargas_windows, nombre_archivo)

            # Variable de control para saber si la descarga tuvo éxito
            descarga_exitosa = False

            # 3. INTERCEPTOR DE RED (Monitorea todo el tráfico en segundo plano)
            def interceptar_pdf(route):
                nonlocal descarga_exitosa
                # Obtenemos la respuesta real del servidor (manejando redirecciones internamente)
                response = route.fetch()
                
                # Verificamos si la respuesta final de la cadena es el archivo PDF
                if response.headers.get("content-type") == "application/pdf":
                    print("¡PDF definitivo interceptado tras la redirección! Guardando...")
                    
                    with open(ruta_final, "wb") as f:
                        f.write(response.body())   # Guardamos los bytes binarios
                    
                    descarga_exitosa = True
                    route.abort()  # Cancelamos la petición en el navegador para que la pestaña no cambie al lector de PDF
                else:
                    route.continue_()  # Si es cualquier otra petición (imágenes, scripts), la dejamos pasar normalmente

            # Activamos el interceptor para cualquier URL que maneje la web ("**" significa cualquier ruta)
            page.route("**/*", interceptar_pdf)

            # 4. Hacer clic en el botón de descarga
            print("Haciendo clic en el botón y procesando flujos de red...")
            page.click('//*[@id="empleadosbundle_asistencia_submit"]')

            # Damos un pequeño margen de tiempo para que se complete la descarga en segundo plano
            page.wait_for_timeout(3000)

            # Desactivamos el interceptor limpiando las rutas
            page.unroute("**/*")

            # 5. Verificación de resultado
            if descarga_exitosa:
                print(f"¡PDF guardado con éxito en: {ruta_final}")
                mensaje_exito = "✅ Script Ejecutado Correctamente: El PDF se interceptó tras la redirección 302 y se guardó con éxito."
                enviar_telegram(mensaje_exito)
            else:
                raise Exception("No se pudo capturar el archivo PDF. La redirección no devolvió un Content-Type válido.")

            time.sleep(2)


        except Exception as e:
            mensaje_error = f"❌ Error durante la automatización: {e}"
            enviar_telegram(mensaje_error)
        
        finally:
            # Cerramos el navegador de forma segura
            print("Cerrando navegador...")
            browser.close()
    
def enviar_telegram(mensaje):
    # En lugar de dejar el texto fijo, leemos las variables de entorno de la máquina virtual
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Error: No se encontraron las credenciales de Telegram en el entorno.")
        return

    url = f"https://telegram.org{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Notificación de Telegram enviada con éxito.")
        else:
            print(f"Telegram rechazó el mensaje: {response.text}")
    except Exception as e:
        print(f"Error al enviar Telegram: {e}")

if __name__ == "__main__":
    iniciar_sesion_y_automatizar()
