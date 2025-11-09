import os
import sys
import telnetlib
import time
import csv
from datetime import datetime
import logging
import requests
import threading
import pyte
from PIL import Image, ImageDraw, ImageFont
import io
from data_processing import actualizar_datos

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

TELEGRAM_BOT_TOKEN = '7085796610:AAFpXJ681zFlYpLM7W_JTdozB0bWfCZ796I'
TELEGRAM_CHAT_ID_ADMIN = '-1001842559779'
TELEGRAM_CHAT_IDS_LIMITED = ['-1002154476162', '-1002155352659']

consulta_en_progreso = threading.Lock()
hilo_actualizacion_activo = False  # Variable para controlar el estado del hilo de actualización

def load_permitted_commands(file_path):
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            comandos_permitidos = [row[0].strip().lower() for row in reader]
        return comandos_permitidos
    except Exception as e:
        logging.error(f"Error al leer el archivo de comandos permitidos: {e}")
        return []

def send_telegram_message(message, chat_id):
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(telegram_api_url, json=payload)
        response.raise_for_status()
        logging.info(f"Mensaje enviado a Telegram en chat ID {chat_id}.")
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Error HTTP al enviar mensaje a Telegram: {http_err}")
    except Exception as err:
        logging.error(f"Error inesperado al enviar mensaje a Telegram: {err}")

def send_telegram_image(image, chat_id):
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with io.BytesIO() as output:
        image.save(output, format="PNG")
        output.seek(0)
        files = {"photo": output}
        payload = {"chat_id": chat_id}
        try:
            response = requests.post(telegram_api_url, data=payload, files=files)
            response.raise_for_status()
            logging.info(f"Imagen enviada a Telegram en chat ID {chat_id}.")
        except Exception as err:
            logging.error(f"Error al enviar imagen a Telegram en chat ID {chat_id}: {err}")

def get_telegram_updates(last_update_id=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 100, "offset": last_update_id}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['result']
    except Exception as err:
        logging.error(f"Error inesperado al obtener actualizaciones de Telegram: {err}")
    return []

def capturar_salida_terminal(tn):
    screen = pyte.Screen(80, 24)  # Asume una terminal de 80x24
    stream = pyte.Stream(screen)
    output = tn.read_very_eager().decode('utf-8', errors='replace')
    stream.feed(output)
    return list(screen.display)

def convertir_a_imagen(lineas):
    font = ImageFont.load_default()
    max_width = max([len(linea) for linea in lineas])
    img = Image.new('RGB', (max_width * 6, len(lineas) * 10), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    for i, linea in enumerate(lineas):
        d.text((0, i * 10), linea, font=font, fill=(0, 0, 0))
    return img

def log_user_action(user_id, username, first_name, last_name, chat_id, command):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "username": username if username else f"{first_name} {last_name}",
        "chat_id": chat_id,
        "command": command
    }
    with open("user_logs.csv", "a", newline='', encoding='utf-8') as csvfile:
        fieldnames = ["timestamp", "user_id", "username", "chat_id", "command"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if csvfile.tell() == 0: 
            writer.writeheader()
        
        writer.writerow(log_entry)
    
    logging.info(f"Registro de usuario: {log_entry}")

def handle_telegram_command(tn, command, chat_id, user_info):
    command = command.strip().lower()  # Convertir el comando a minúsculas para compararlo
    comandos_permitidos = load_permitted_commands('C:\\UTCV4.1\\comandos.csv')  # Cargar comandos desde el archivo CSV

    # Verificar si el mensaje empieza con '- '
    if command.startswith('- '):
        comando_telnet = command[2:].strip()  # Eliminar '- ' y espacios adicionales
        comando_principal = comando_telnet.split()[0]  # Obtener el primer elemento del comando

        # Verificar si el comando está en la lista de permitidos
        if comando_principal not in comandos_permitidos:
            send_telegram_message(f"El comando '{comando_principal}' no está permitido.", chat_id)
            logging.warning(f"Intento de comando no permitido: '{comando_telnet}' desde chat ID {chat_id}")
            return  # Termina la función aquí si no está permitido
        
        logging.info(f"Comando permitido para Telnet: '{comando_telnet}' desde chat ID: {chat_id} por usuario: {user_info['username'] if user_info['username'] else f'{user_info['first_name']} {user_info['last_name']}'}")
        log_user_action(user_info['id'], user_info['username'], user_info['first_name'], user_info['last_name'], chat_id, comando_telnet)

        if consulta_en_progreso.locked():
            send_telegram_message("Ya hay una consulta en curso. Por favor, espera a que se complete.", chat_id)
            logging.warning(f"Consulta bloqueada: '{comando_telnet}' desde chat ID {chat_id} porque hay una consulta en curso.")
            return  # Termina la función aquí si está bloqueada
        
        with consulta_en_progreso:
            try:
                tn.write(f'{comando_telnet}\r\n'.encode('utf-8'))
                time.sleep(5)  # Espera 5 segundos para asegurarse de que toda la salida se ha recibido
                lineas = capturar_salida_terminal(tn)
                imagen = convertir_a_imagen(lineas)
                send_telegram_image(imagen, chat_id)
            except Exception as e:
                send_telegram_message(f"Error ejecutando comando en Telnet: {e}", chat_id)
                logging.error(f"Error ejecutando comando en Telnet desde chat ID {chat_id}: {e}")
                if "10054" in str(e):  # Detecta específicamente el error WinError 10054
                    restart_script()
    else:
        # Notificar al usuario que los comandos deben comenzar con '- '
        send_telegram_message("Para enviar comandos al Telnet, el mensaje debe comenzar con '- ' seguido del comando.", chat_id)

def restart_script():
    logging.info("Reiniciando el script debido a un error crítico en la conexión Telnet.")
    os.execv(sys.executable, ['python'] + sys.argv)

def iniciar_conexion():
    host = "172.30.1.26"
    port = 23
    tn = None
    
    while True: 
        try:
            mensaje_intento = "Intentando establecer conexión Telnet..."
            send_telegram_message(mensaje_intento, TELEGRAM_CHAT_ID_ADMIN)
            for chat_id in TELEGRAM_CHAT_IDS_LIMITED:
                send_telegram_message(mensaje_intento, chat_id)
            
            tn = telnetlib.Telnet(host, port)
            tn.read_until(b"MS Windows Server 4.0  (TCC-G) ()", timeout=10).decode('utf-8', errors='replace')
            tn.write(b'bramal\r\n')
            tn.write(b'Sistema.bramal1541\r\n')
            tn.write(b'trof\r\n')  # Enviar 'trof' como el primer comando después de reconectar
            tn.read_until(b"Successfully logged in!", timeout=10).decode('utf-8', errors='replace')
            
            mensaje_exito = "Conexión Telnet establecida exitosamente."
            send_telegram_message(mensaje_exito, TELEGRAM_CHAT_ID_ADMIN)
            for chat_id in TELEGRAM_CHAT_IDS_LIMITED:
                send_telegram_message(mensaje_exito, chat_id)
            
            logging.info("Conexión Telnet establecida con éxito.")
            return tn 
        except EOFError:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mensaje = f"[{current_time}] La conexión Telnet se cerró inesperadamente. Intentando reconectar..."
            logging.error(mensaje)
            send_telegram_message(mensaje, TELEGRAM_CHAT_ID_ADMIN)
            for chat_id in TELEGRAM_CHAT_IDS_LIMITED:
                send_telegram_message(mensaje, chat_id)
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mensaje = f"[{current_time}] Ocurrió un error: {e}. Intentando reconectar..."
            logging.error(mensaje)
            send_telegram_message(mensaje, TELEGRAM_CHAT_ID_ADMIN)
            for chat_id in TELEGRAM_CHAT_IDS_LIMITED:
                send_telegram_message(mensaje, chat_id)
        finally:
            if tn and tn.eof:
                tn.close()
                tn = None
        time.sleep(5)

def ejecutar_actualizar_datos(tn):
    global hilo_actualizacion_activo  # Usa la variable global para controlar el estado del hilo
    if hilo_actualizacion_activo:
        return  # Si ya hay un hilo de actualización corriendo, no se crea otro

    hilo_actualizacion_activo = True  # Marcamos el hilo como activo

    try:
        while True:
            if not actualizar_datos(tn, "J000000"):
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logging.warning(f"[{current_time}] NO SE RECIBIERON DATOS")
                send_telegram_message(f"[{current_time}] NO SE RECIBIERON DATOS. Reintentando conexión...", TELEGRAM_CHAT_ID_ADMIN)
                tn.close()  # Cerramos la conexión anterior
                tn = iniciar_conexion()  # Reintentamos la conexión
            time.sleep(60)
    except Exception as e:
        logging.error(f"Error durante la actualización de datos: {e}")
        send_telegram_message(f"Error durante la actualización de datos: {e}. Reintentando conexión...", TELEGRAM_CHAT_ID_ADMIN)
        tn.close()
        tn = iniciar_conexion()
    finally:
        hilo_actualizacion_activo = False  # Marcamos el hilo como inactivo al terminar

def mantener_conexion(actualizar_datos):
    last_update_id = None
    
    while True:
        tn = iniciar_conexion()
        if tn:
            thread_actualizar = threading.Thread(target=ejecutar_actualizar_datos, args=(tn,))
            thread_actualizar.start()

            while tn and not tn.eof:
                updates = get_telegram_updates(last_update_id)
                if updates:
                    last_update_id = updates[-1]['update_id'] + 1
                    for update in updates:
                        message = update.get('message')
                        if message:
                            chat_id = message['chat']['id']
                            text = message.get('text')
                            if text:
                                user_info = {
                                    'id': message['from']['id'],
                                    'username': message['from'].get('username', None),
                                    'first_name': message['from'].get('first_name', ''),
                                    'last_name': message['from'].get('last_name', '')
                                }
                                logging.info(f"Mensaje recibido: '{text}' desde chat ID: {chat_id}")
                                handle_telegram_command(tn, text.strip(), chat_id, user_info)
            tn = None
            logging.info("La conexión se perdió, reiniciando ciclo de conexión...")
        else:
            mensaje = "No se pudo establecer una conexión. Reintentando..."
            logging.error(mensaje)
            send_telegram_message(mensaje, TELEGRAM_CHAT_ID_ADMIN)
            for chat_id in TELEGRAM_CHAT_IDS_LIMITED:
                send_telegram_message(mensaje, chat_id)
            time.sleep(5)

if __name__ == "__main__":
    mantener_conexion(actualizar_datos)
