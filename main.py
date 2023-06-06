__author__ = 'Eitan Melnitzky'
# EL COMANDO EN TERMINAL PARA EXPORTAR ESTO EN UN SOLO ARCHIVO .EXE ES: pyinstaller main.py --onefile

from os import listdir, path, remove
from time import sleep
from sys import exit
import logging
import stock_download as sd
import acciones as acc
import graficos as gr
import portfolios as pf


def limpiar_carpeta(path_f):
    for item in listdir(path_f):
        remove(f'{path_f}/{item}')


def main():
    print('\n---------- Bienvenido ----------\n')

    try:
        # Busco el portfolio actualizado por ultima vez. Este solo tiene las posiciones abiertas.
        port_actual = pf.levantar_portfolio('Seguimiento/ultimo_portfolio.csv')
        # Busco el portfolio historico actualizado por ultima vez. Este tiene tanto posiciones abiertas como cerradas
        port_historico = pf.levantar_portfolio('Seguimiento/ultimo_historico.csv')
    except:
        print('Error al levantar portfolios')
        sleep(5)
        exit()

    try:
        # Actualizo los portfolios con las operaciones desde la ultima actualizacion hasta el momento
        port_actual.actualizar_portfolio(log_entry='ultima_actu_portfolio', guarda_cerradas=False)
        port_historico.actualizar_portfolio(log_entry='ultima_actu_historico', guarda_cerradas=True)
        print('- Tenencias actualizadas')
    except:
        print('Error al actualizar portfolios')
        sleep(5)
        exit()

    try:
        # Actualizo los precios de las acciones abiertas de los dos porfolios
        port_actual.actualizar_precios(cambiar_cash=True)
        port_historico.actualizar_precios(cambiar_cash=False)
        print('- Precios actualizados')
    except:
        print('Error al actualizar precios de acciones en portfolios')
        sleep(5)
        exit()

    try:
        # GUARDAR LOS PORTFOLIOS: CHEQUEAR SI EN ALGUN MOMENTO SE GENERA LA CARPETA SEGUIMIENTO
        pf.bajar_portfolio(port_actual, path_f='Seguimiento/ultimo_portfolio.csv')
        pf.bajar_portfolio(port_historico, path_f='Seguimiento/ultimo_historico.csv')
    except:
        print('Error al guardar portfolios')
        sleep(5)
        exit()

    try:
        # Grafico el porfolio actual
        gr.grafico_portfolio(port_actual, archivo='Tenencias', definicion=800)
        print(f'- Tus tenencias actuales fueron graficadas en Seguimiento/Tenencias.jpg')
    except:
        print('Error al graficar portfolio actual')
        sleep(5)
        exit()

    try:
        # Elimino los archivos de la carpeta que contiene los csv, para evitar que se acumulen archivos sin actualizar
        if 'Stocks Data' in listdir('.'):
            limpiar_carpeta('Stocks Data')
        # Elimino los archivos de la carpeta que contiene los gráficos, para evitar que se acumulen graficos sin actualizar
        if 'Stocks Grafs' in listdir('.'):
            limpiar_carpeta('Stocks Grafs')
    except:
        print('Error al eliminar info de Stocks')
        sleep(5)
        exit()

    try:
        # Bajada de las acciones. Esto implica:
        #   - gestion de token
        #   - descarga de series historicas
        #   - enriquecimiento de las series con indicadores
        #   - guardado de los archivos de series historicas
        #   - guardado del archivo de resumen con una linea por papel
        #   - guardado de reporte de descargas exitosas y fallidas
        estado_descarga = sd.stck_dwnld_iol(acc.stocks)
        fallidas = [elemento[0] for elemento in estado_descarga[1]]
    except:
        print('Error al bajar series historicas de iol')
        sleep(5)
        exit()

    try:
        # Grafico los ultimos 180 dias de todas las acciones que han tenido descargas de su serie historica con 800dpi
        gr.graficos_velas(dias=180, definicion=800)
    except:
        print('Error al hacer graficos de velas')
        sleep(5)
        exit()

    try:
        # Linea final del script borrando el token (chequear cuan necesaria pueda ser...)
        if path.exists('token.txt'):
            remove('token.txt')
    except:
        print('Error al eliminar token file')
        sleep(5)
        exit()

    print('\n-------- Muchas Gracias --------')
    sleep(3)


if __name__ == '__main__':
    logging.basicConfig(filename='Logs/events.log', filemode='w', encoding='utf-8',
                        level=logging.INFO,
                        format='%(levelname)s - %(asctime)s - %(filename)s, %(funcName)s, line%(lineno)d: %(message)s',
                        datefmt='%H:%M:%S'
                        )

    logging.info('Empieza ejecución general')
    main()
    logging.info('Finaliza ejecución general')

