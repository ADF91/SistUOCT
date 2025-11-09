# import re
# import json
# import requests
# import time
# from datetime import datetime
# from utils import log_api_message, clean_ansi

# urlUpdate = 'https://api-bramal.com/update/uoct/semaforo/'

# session = requests.Session()  # Inicializar una sesión de requests

# def actualizar_envio_db():
#     with open('ActualizacionDB', 'r', encoding='utf-8') as archivo_actualizacion:
#         identificadores = {linea.split(',')[0] for linea in archivo_actualizacion}

#     datos_para_enviar = []
#     with open('EnvioDB', 'w', encoding='utf-8') as archivo_envio:
#         with open('J000000.txt', 'r', encoding='utf-8') as archivo_j:
#             for linea in archivo_j:
#                 resultado_busqueda = re.search(r'(J\d{6}).*(is .+)', linea)
#                 if resultado_busqueda:
#                     identificador = resultado_busqueda.group(1)
#                     info = resultado_busqueda.group(2)
#                     info_limpia = clean_ansi(info).strip()

#                     if identificador in identificadores:
#                         archivo_envio.write(f'{identificador} {info_limpia}\n')
#                         datos_para_enviar.append({"codSemaforo": identificador, "leyenda": info_limpia})
    
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     print(f'[{current_time}] Actualizacion Enviada')
   
#     return datos_para_enviar

# def enviar_elemento(elemento):
#     elemento['leyenda'] = clean_ansi(elemento['leyenda'])

#     try:
#         elemento_json = json.dumps(elemento)
#         log_api_message(elemento)

#         response = session.put(
#             url=urlUpdate + elemento['codSemaforo'],
#             data=elemento_json,
#             headers={'Content-Type': 'application/json'},
#             timeout=10
#         )
#         response.raise_for_status()
#         current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         print(f"[{current_time}] Datos enviados correctamente: HTTP {response.status_code}")
#     except requests.exceptions.HTTPError as http_err:
#         print(f"Error HTTP: {http_err}")
#     except Exception as error:
#         print(f"Error al enviar datos: {error}")

# def main():
#     datos_para_enviar = actualizar_envio_db()
#     for dato in datos_para_enviar:
#         enviar_elemento(dato)

# if __name__ == "__main__":
#     main()



#################################################################

import re
import json
import requests
from datetime import datetime
from utils import log_api_message, clean_ansi

# URLs de destino
urlUpdate = 'https://api-bramal.com/update/uoct/semaforo/'  # API externa
urlFastAPI = 'https://api-bramal.com/microservicio/update_uoct/'            # Tu FastAPI local en puerto 8000

# Inicializar una sesión HTTP reutilizable
session = requests.Session()

def actualizar_envio_db():
    """Lee archivo J000000.txt y genera datos a enviar basados en coincidencias con ActualizacionDB"""
    with open('ActualizacionDB', 'r', encoding='utf-8') as archivo_actualizacion:
        identificadores = {linea.split(',')[0] for linea in archivo_actualizacion}

    datos_para_enviar = []
    with open('EnvioDB', 'w', encoding='utf-8') as archivo_envio:
        with open('J000000.txt', 'r', encoding='utf-8') as archivo_j:
            for linea in archivo_j:
                resultado_busqueda = re.search(r'(J\d{6}).*(is .+)', linea)
                if resultado_busqueda:
                    identificador = resultado_busqueda.group(1)
                    info = resultado_busqueda.group(2)
                    info_limpia = clean_ansi(info).strip()

                    if identificador in identificadores:
                        archivo_envio.write(f'{identificador} {info_limpia}\n')
                        datos_para_enviar.append({
                            "codSemaforo": identificador,
                            "leyenda": info_limpia
                        })
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'[{current_time}] ✅ Procesamiento completado. Elementos listos para enviar.')

    return datos_para_enviar

def enviar_elemento(elemento):
    """Envía un dato a dos APIs: la externa y tu FastAPI local"""
    elemento['leyenda'] = clean_ansi(elemento['leyenda'])

    try:
        elemento_json = json.dumps(elemento)
        log_api_message(elemento)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Envío a API externa
        response = session.put(
            url=urlUpdate + elemento['codSemaforo'],
            data=elemento_json,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        print(f"[{current_time}] 🌐 Enviado a API externa: HTTP {response.status_code}")

        response_local = session.put(
            url=urlFastAPI + elemento['codSemaforo'],
            data=elemento_json,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response_local.raise_for_status()
        print(f"[{current_time}] 🚀 Enviado a FastAPI local: HTTP {response_local.status_code}")

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Error HTTP: {http_err}")
    except Exception as error:
        print(f"❌ Error general al enviar datos: {error}")

def main():
    datos_para_enviar = actualizar_envio_db()
    for dato in datos_para_enviar:
        enviar_elemento(dato)

if __name__ == "__main__":
    main()
