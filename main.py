from telnet_manager import mantener_conexion
from data_processing import actualizar_datos

if __name__ == "__main__":
    print('Iniciando el proceso de actualización y monitoreo de datos...')
    mantener_conexion(actualizar_datos)