from os import listdir, mkdir
from json import loads
import logging


# Si el log nunca existio, lo crea por primera vez con el contenido que se le pase
def actualizar_log(json_log):
    logging.info('Se actualiza el archivo de logs')
    # Si no existe una carpeta de logs, se crea
    if 'Logs' not in listdir('.'):
        mkdir('Logs')
    with open('Logs/logs.txt', 'w') as archivo:
        archivo.writelines(str(json_log))


# Si el log existe, lo busca y lo devuelve. Si no existe, devuelve un diccionario vacío para trabajar con el y llenarlo
def buscar_log():
    logging.info('Se busca los últimos logs')
    if 'Logs' in listdir('.'):
        if 'logs.txt' in listdir('Logs'):
            with open('Logs/logs.txt', 'r') as archivo:
                log = loads(archivo.readline().strip().replace("'", '"'))
            return log
        else:
            return dict()
    else:
        return dict()
