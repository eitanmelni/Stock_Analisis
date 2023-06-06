from datetime import datetime
from pandas import DataFrame, DatetimeIndex
from json import loads
from os import listdir, mkdir
import logging
import iol
import funciones as fs
import acciones as acc


def stck_dwnld_iol(stock_list=acc.stocks):
    logging.info('Se comienza a descargar las series historicas')
    # Gestiono el token
    iol.gestor_token()
    # Defino variables generales para hacer el llamado a la api en todos los casos: fechas y mercado de interés
    mercado = 'bCBA'
    start = '2022-05-18'
    end = datetime.today().date()
    # preparo los nombre de las columnas con la información que me interesa conservar
    columns = ['Open', 'High', 'Low', 'Adj Close', 'Volume']
    # preparo listas con las acciones que baje con código exitoso y con código de error
    exitosas = []
    fail_download = []
    # preparo las listas para luego armar eldataframe de resumen, donde estará la info del último día de cada accion
    tickers = []
    resumen = []
    columns_resumen = columns + ['MACD', 'Signal', 'Histogram', 'RSI', 'LocalMax', 'LocalMin', 'AbsMax',
                                 'Volatilidad Vela', 'Amplitud Vela porcent']
    print('\nSTATUS DESCARGA:')
    # Loop para descargar la serie histórica de todos los papeles que están definidos en acciones.py
    for stock in stock_list:
        token = iol.gestor_token()
        # Usando la funcion serie_hist generamos guardo la respuesta de la API para la accion
        historico = iol.serie_hist(stock, token, start, end, mercado)
        # Inicializo los index de lo que será el dataframe (que contendra las fechas) y la data (que guardará las lineas
        # de la serie historica con los valores con los que previamente se creo la lista de columns)
        index = []
        data = []
        # En caso que la bajada sea exitosa
        if historico.status_code in [200, 201] and len(loads(historico.text)) > 0:
            # Updateo el status para que el usuario siga el progreso
            print(f'- {stock}: exitosa')
            # Guardo el papel en la lista "existosas"
            exitosas.append(stock)
            # Proceso el json con la serie historica de la accion
            json_hist = loads(historico.text)
            for i in range(1, len(json_hist) + 1):
                index.append(json_hist[-i]['fechaHora'].split('T')[0])
                data.append([json_hist[-i]['apertura'],
                             json_hist[-i]['maximo'],
                             json_hist[-i]['minimo'],
                             json_hist[-i]['ultimoPrecio'],
                             json_hist[-i]['volumenNominal']])
            # Armo el dataframe de la accion siempre con las mismas columnas y con las fechas y data que se obtuvo
            # en la serie
            df = DataFrame(data, index=DatetimeIndex(index), columns=columns)
            # ENRIQUECIMIENTO: Agrego el MACD y RSI. Agrego el max y min local, el max de la serie historica y el
            # tipo de vela
            # Luego guardo los archivos en una nueva carpeta para almacenarlos
            df = fs.macd(df)
            df = fs.rsi(df)
            df = fs.extremos_locales(df)
            df = fs.extremos_hist(df)
            df = fs.velas_categ(df)
            # Sumo la info de la accion actual del loop a las listas del resumen
            tickers.append(stock)
            resumen.append(df.iloc[-1])
            if 'Stocks Data' not in listdir('.'):
                mkdir('Stocks Data')
            df.to_csv(f'Stocks Data\\{acc.tickers[stock]}.csv', index=True, index_label='Fecha')
        # En caso que la bajada devuelva un error, solamente se guarda la accion y el error en la lista "fail_download"
        else:
            # Updateo el status para que el usuario siga el progreso
            print(f'- {stock}: fallida')
            fail_download.append([stock, historico.status_code])
    # Creo el dframe de resumen con una linea por accion donde el index es el ticker y la data es la info del ultimo dia
    resumen_acciones = DataFrame(resumen, index=tickers, columns=columns_resumen)
    resumen_acciones.to_csv('Resumen_Acciones.csv', index=True, index_label='Accion')
    # Como resultado solo se devuelve las listas con exitos y errores, pero ademas la funcion tiene el trabajo de crear
    # los archivos con las series historicas de las descargas exitosas
    with open('stck_dwnld.txt', 'w') as archivo:
        # Escribir cada elemento de la lista en una línea separada del archivo
        archivo.writelines("EXITOSAS:\n")
        archivo.writelines("%s\n" % elemento for elemento in exitosas)
        archivo.writelines("\n")
        archivo.writelines("FALLIDAS:\n")
        archivo.writelines("%s\n" % elemento for elemento in fail_download)
    return [exitosas, fail_download]


'''
LA IDEA ES HACER UN PLAN B PARA LAS ACCIONES QUE DEVUELVEN CODIGOS DE ERROR O RESPUESTAS VACIAS EN LA FUNCION ANTERIOR
    - BUSCAR CUALES SON LAS ACCIONES EN CUESTION
    - BUSCAR CUAL ES LA ULTIMA FECHA DE LA QUE SE TIENE INFORMACION HISTORICA DE CADA PAPEL (DEBEN ESTAR GUARDADOS COMO 
    INFO PERMANENTE QUE NO SE RENUEVA A CADA CORRIDA DEL SCRIPT)
    - CONSULTAR LA COTIZACION DIA POR DIA DESDE LA ULTIMA INFO HASTA EL DIA ACTUAL/ANTERIOR Y ALMACENARLA PARA QUE LUEGO
    PUEDA SER GRAFICADA
'''

'''
QUIZAS, EN LUGAR DE UN PLAN B, SE PUEDE CONSEGUIR UN SITIO (ALPHA VANTAGE, POR EJEMPLO) PARA CONSEGUIR INFO HISTORICA DE
EMPRESAS Y MEDIANTE UN MODELO DE MACHINE LEARNING UBICAR LAS ACCIONES CON MAS PROBABLIDADES DE SUBIR EN LOS PROXIMOS 
TIEMPOS
'''

'''def stck_dwnld_alpha(tickers):
    pass'''
