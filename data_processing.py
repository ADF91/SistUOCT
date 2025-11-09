import re
import os
import time
from datetime import datetime
from SemaforoSQL import ejecutar_script_semaforo
from Comparativo import procesar_archivos
from EnvioDB import main as envio_db_main
import logging

ansi_escape = re.compile(r'\x1B[@-_][0-?]*[@-~]')

def clean_ansi_sequences(text):
    return ansi_escape.sub('', text)

def save_and_close_csv(data, filename):
    with open(filename, "w", encoding='utf-8') as file:
        file.write(clean_ansi_sequences(data) + "\n")
        

def get_file_size_kb(filename):
    return os.path.getsize(filename) / 1024

def actualizar_datos(tn, elemento):
    nombreArchivo = f"{elemento}.txt"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f'[{current_time}] ACT. ARCHIVO: {nombreArchivo}')
    tn.write(f'lsts {elemento}\r\n'.encode('utf-8'))

    buffer = ""
    last_read_time = time.time()
    try:
        while True:
            try:
                salida_parcial = tn.read_very_eager().decode('utf-8', errors='replace')
                buffer += salida_parcial
                if salida_parcial.endswith('>'):
                    break
                if time.time() - last_read_time > 2:
                    break
                if not salida_parcial:
                    time.sleep(1)
                else:
                    last_read_time = time.time()
            except ConnectionAbortedError as e:
                logging.error(f'[{current_time}] Conexión abortada: {e}. Reiniciando conexión...')
                return False
    except EOFError:
        logging.error(f'[{current_time}] Conexión Telnet cerrada inesperadamente. Reiniciando conexión...')
        return False

    if buffer.strip():
        save_and_close_csv(buffer, nombreArchivo)
        ejecutar_script_semaforo()
        procesar_archivos()
        envio_db_main()

        # Elimina o comenta el bloque de código a continuación
        # if get_file_size_kb(nombreArchivo) < 100:
        #     logging.error(f"[{current_time}] El archivo es menor a 100KB, reiniciando la conexión Telnet.")
        #     return False

        return True
    else:
        logging.warning(f'[{current_time}] NO SE RECIBIERON DATOS')
        return False
