__author__ = 'Eitan Melnitzky'
# EL COMANDO EN TERMINAL PARA EXPORTAR ESTO EN UN SOLO ARCHIVO .EXE ES: pyinstaller main.py --onefile

import stock_download as sd
import acciones as acc
import graficos as gr
import os
import portfolios as pf
import time as tm
import sys


def limpiar_carpeta(path):
    for item in os.listdir(path):
        os.remove(f'{path}/{item}')


print('\n---------- Bienvenido ----------\n')

try:
    # Busco el portfolio actualizado por ultima vez. Este solo tiene las posiciones abiertas.
    port_actual = pf.levantar_portfolio('Seguimiento/ultimo_portfolio.csv')
    # Busco el portfolio historico actualizado por ultima vez. Este tiene tanto posiciones abiertas como cerradas
    port_historico = pf.levantar_portfolio('Seguimiento/ultimo_historico.csv')
except:
    print('Error al levantar portfolios')
    tm.sleep(5)
    sys.exit()

try:
    # Actualizo los portfolios con las operaciones desde la ultima actualizacion hasta el momento
    port_actual.actualizar_portfolio(log_entry='ultima_actu_portfolio', guarda_cerradas=False)
    port_historico.actualizar_portfolio(log_entry='ultima_actu_historico', guarda_cerradas=True)
    print('- Tenencias actualizadas')
except:
    print('Error al actualizar portfolios')
    tm.sleep(5)
    sys.exit()

try:
    # Actualizo los precios de las acciones abiertas de los dos porfolios
    port_actual.actualizar_precios(cambiar_cash=True)
    port_historico.actualizar_precios(cambiar_cash=False)
    print('- Precios actualizados')
except:
    print('Error al actualizar precios de acciones en portfolios')
    tm.sleep(5)
    sys.exit()

try:
    # GUARDAR LOS PORTFOLIOS: CHEQUEAR SI EN ALGUN MOMENTO SE GENERA LA CARPETA SEGUIMIENTO
    pf.bajar_portfolio(port_actual, path='Seguimiento/ultimo_portfolio.csv')
    pf.bajar_portfolio(port_historico, path='Seguimiento/ultimo_historico.csv')
except:
    print('Error al guardar portfolios')
    tm.sleep(5)
    sys.exit()

try:
    # Grafico el porfolio actual
    gr.grafico_portfolio(port_actual, archivo='Tenencias', definicion=800)
    print(f'- Tus tenencias actuales fueron graficadas en Seguimiento/Tenencias.jpg')
except:
    print('Error al graficar portfolio actual')
    tm.sleep(5)
    sys.exit()

try:
    # Elimino los archivos de la carpeta que contiene los csv, para evitar que se acumulen archivos sin actualizar
    if 'Stocks Data' in os.listdir('.'):
        limpiar_carpeta('Stocks Data')
    # Elimino los archivos de la carpeta que contiene los gráficos, para evitar que se acumulen graficos sin actualizar
    if 'Stocks Grafs' in os.listdir('.'):
        limpiar_carpeta('Stocks Grafs')
except:
    print('Error al eliminar info de Stocks')
    tm.sleep(5)
    sys.exit()

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
    tm.sleep(5)
    sys.exit()

try:
    # Grafico los ultimos 180 dias de todas las acciones que han tenido descargas de su serie historica con 800dpi
    gr.graficos_velas(dias=180, definicion=800)
except:
    print('Error al hacer graficos de velas')
    tm.sleep(5)
    sys.exit()

try:
    # Linea final del script borrando el token (chequear cuan necesaria pueda ser...)
    if os.path.exists('token.txt'):
        os.remove('token.txt')
except:
    print('Error al eliminar token file')
    tm.sleep(5)
    sys.exit()

print('\n-------- Muchas Gracias --------')
tm.sleep(3)
