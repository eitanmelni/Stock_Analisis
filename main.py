__author__ = 'Eitan Melnitzky'
# EL COMANDO EN TERMINAL PARA EXPORTAR ESTO EN UN SOLO ARCHIVO .EXE ES: pyinstaller main.py --onefile
# COMANDOS DE GIT PARA ACTUALIZAR EL REPOSITORIO ONLINE:
# git init
# git add .
# git commit -m "MENSAJE DE LOS CAMBIOS"
# git push origin main
# SI SE QUIERE RETROTRAER UN ADD
# git reset
# SI SE QUIERE CHEQUEAR UN COMMIT
# git log
# SI SE QUIERE CANCELAR UN COMMIT
# git reset HEAD~
import stock_download as sd
import acciones as acc
import graficos as gr
import os
import portfolios as pf
import time as tm


def limpiar_carpeta(path):
    for item in os.listdir(path):
        os.remove(f'{path}/{item}')


print('---------- Bienvenido ----------')

# Busco el portfolio actualizado por ultima vez. Este solo tiene las posiciones abiertas.
port_actual = pf.levantar_portfolio('Seguimiento/ultimo_portfolio.csv')

# Busco el portfolio historico actualizado por ultima vez. Este tiene tanto posiciones abiertas como cerradas
port_historico = pf.levantar_portfolio('Seguimiento/ultimo_historico.csv')

# Actualizo los portfolios con las operaciones desde la ultima actualizacion hasta el momento
port_actual.actualizar_portfolio(log_entry='ultima_actu_portfolio', guarda_cerradas=False)
port_historico.actualizar_portfolio(log_entry='ultima_actu_historico', guarda_cerradas=True)
print('- Tenencias actualizadas')

# Actualizo los precios de las acciones abiertas de los dos porfolios
port_actual.actualizar_precios(cambiar_cash=True)
port_historico.actualizar_precios(cambiar_cash=False)
print('- Precios actualizados')

# GUARDAR LOS PORTFOLIOS: CHEQUEAR SI EN ALGUN MOMENTO SE GENERA LA CARPETA SEGUIMIENTO
pf.bajar_portfolio(port_actual, path='Seguimiento/ultimo_portfolio.csv')
pf.bajar_portfolio(port_historico, path='Seguimiento/ultimo_historico.csv')

# Grafico el porfolio actual
gr.grafico_portfolio(port_actual, archivo='Tenencias', definicion=800)
print(f'- Tus tenencias actuales fueron graficadas en Seguimiento/Tenencias.jpg')

# Elimino los archivos de la carpeta que contiene los csv, para evitar que se acumulen archivos sin actualizar
if 'Stocks Data' in os.listdir('.'):
    limpiar_carpeta('Stocks Data')
# Elimino los archivos de la carpeta que contiene los gráficos, para evitar que se acumulen graficos sin actualizar
if 'Stocks Grafs' in os.listdir('.'):
    limpiar_carpeta('Stocks Grafs')


# Bajada de las acciones. Esto implica:
#   - gestion de token
#   - descarga de series historicas
#   - enriquecimiento de las series con indicadores
#   - guardado de los archivos de series historicas
#   - guardado del archivo de resumen con una linea por papel
#   - guardado de reporte de descargas exitosas y fallidas
sd.stck_dwnld_iol(acc.stocks)

# Grafico los ultimos 180 dias de todas las acciones que han tenido descargas de su serie historica con 800dpi
gr.graficos_velas(dias=180, definicion=800)

# Linea final del script borrando el token chequear cuand necesaria pueda ser...
os.remove('token.txt')

print('-------- Muchas Gracias --------')
tm.sleep(3)
