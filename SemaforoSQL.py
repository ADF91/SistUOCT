import mysql.connector
import csv
import time
import os
from datetime import datetime

def ejecutar_script_semaforo():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'[{current_time}] Iniciando script MySQL')

    config = {
        'host': 'semaforos.c9v9mosexbyx.us-east-2.rds.amazonaws.com',
        'user': 'admin',
        'password': 'Semaforos123',
        'database': 'semaforo',
        'port': '3306',
        'auth_plugin': 'mysql_native_password'
    }

    script_dir = os.path.dirname(__file__)
    csv_file_path = os.path.join(script_dir, 'SemaforosSQL.csv')
    csv_file_path2 = os.path.join(script_dir, 'SemaforosSQL2.csv')

    lista_negra = ['J000000']

    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        time.sleep(5)

        query = "SELECT codSemaforo, utcSensor FROM `semaforo`.`semaforos`;"
        cursor.execute(query)

        rows = cursor.fetchall()
        filtered_rows = [row for row in rows if row[0] not in lista_negra]

        with open(csv_file_path, "w", newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([i[0] for i in cursor.description])  # Escribir encabezados
            csv_writer.writerows(filtered_rows)  # Escribir las filas filtradas

        # INICIO DE ACTUALIZACION
        # Query para la segunda base de datos:
        query2 = '''
        SELECT S.JUNTION AS codSemaforo, M.UTC AS utcSensor
        FROM MONITOREO.ULT_ACT_FIN_ILON AS M
        INNER JOIN ACTIVOS.NODO_SEMAFORO AS S ON M.ID_NODO = S.ID
        '''
        cursor.execute(query2)

        row = cursor.fetchall()
        filtered_row = [x for x in row if x[0] not in lista_negra]

        with open(csv_file_path2, 'w', newline='', encoding='utf-8') as csv_file2:
            csv_writer = csv.writer(csv_file2)
            csv_writer.writerow([i[0] for i in cursor.description])
            csv_writer.writerows(filtered_row)
        # FIN DE ACTUALIZACION

    except mysql.connector.Error as e:
        print(f'[{current_time}] Conexion MySQL Cerrada: {e}')
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print(f'[{current_time}] Conexion MySQL Cerrada')
