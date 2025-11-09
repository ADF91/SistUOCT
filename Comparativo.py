import csv
import time
from datetime import datetime
import chardet

def transformar_estado(estado):
    if estado == "Isolated":
        return 0
    elif estado in ["Background", "SCOOT", "Operational"]:
        return 1
    else:
        return -1

def procesar_archivos():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'[{current_time}] Compárativo iniciado')

    datos_sql = {}
    datos_sql2 = {} # Tupla para los datos de la segunda base de datos
    with open('SemaforosSQL.csv', 'r', encoding='utf-8') as archivo_sql:
        reader_sql = csv.reader(archivo_sql)
        next(reader_sql)  # Saltar la cabecera
        for fila in reader_sql:
            if len(fila) >= 2:
                datos_sql[fila[0]] = int(fila[1])

    # INICIO DE ACTUALIZACION
    # Procedemos a leer los datos de la segunda data base
    # with open('SemaforosSQL2.csv', 'r', encoding='utf-8') as archivo_sql2:
    #     reader_sql = csv.reader(archivo_sql2)
    #     next(reader_sql)
    #     for fila in reader_sql:
    #         if len(fila) >= 2:
    #             datos_sql2[fila[0]] = int(fila[1])
    # FIN DE ACTUALIZACION


    with open('J000000.txt', 'rb') as rawfile:
        rawdata = rawfile.read()
        encoding = chardet.detect(rawdata)['encoding']


    with open('J000000.txt', 'r', encoding=encoding) as archivo_j:
        lineas_escritas = set()
        with open('ActualizacionDB', 'w', encoding='utf-8') as archivo_actualizacion:
            for linea in archivo_j:
                for clave, valor_estado_sql in datos_sql.items():
                    if clave in linea:
                        estado = None
                        if "Isolated" in linea:
                            estado = "Isolated"
                        elif "Background" in linea:
                            estado = "Background"
                        elif "SCOOT" in linea:
                            estado = "SCOOT"

                        if estado:
                            valor_estado = transformar_estado(estado)
                            if valor_estado != -1 and valor_estado != valor_estado_sql:
                                linea_verificacion = f'{clave},{valor_estado}\n'
                                if linea_verificacion not in lineas_escritas:
                                    archivo_actualizacion.write(linea_verificacion)
                                    lineas_escritas.add(linea_verificacion)
        
        # with open('ActualizacionDB2', 'w', encoding='utf-8') as archivo_actualizacion2:
        #     for linea in archivo_j:
        #         for clave, valor_estado_sql in datos_sql2.items():
        #             if clave in linea:
        #                 estado = None
        #                 if 'Isolated' in linea:
        #                     estado = 'Isolated'
        #                 elif 'Background' in linea:
        #                     estado = 'Background'
        #                 elif 'SCOOT' in linea:
        #                     estado = 'SCOOT'
                        
        #                 if estado:
        #                     valor_estado = transformar_estado(estado)
        #                     if valor_estado != -1 and valor_estado != valor_estado_sql:
        #                         linea_verificacion = f'{clave},{valor_estado}\n'
        #                         if linea_verificacion not in lineas_escritas:
        #                             archivo_actualizacion2.write(linea_verificacion)
        #                             lineas_escritas.add(linea_verificacion)
    
    

    #*****
    # with open('J000000.txt', 'rb') as rawfile2:
    #     rawdata = rawfile2.read()
    #     encoding = chardet.detect(rawdata)['encoding']
    # INICIO DE ACTUALIZACION

    # with open('J000000.txt', 'r', encoding=encoding) as archivo_j2:
    #     lineas_escritas = set()
    #     

    print(f'[{current_time}] Archivo EnvioDB Actualizado')
