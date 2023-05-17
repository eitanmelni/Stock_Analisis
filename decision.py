import acciones as acc, funciones as fs, iol
import pandas as pd, math


def asignacion(token):
    minimo_inversion = 1500
    maximo_inversion = 10000
    # Se obtiene el dataframe con las acciones que se identificaron como una oportunidad
    oportunidades = fs.analisis_macd(acc.stocks)

    # Se identifica el dinero disponible para operar
    disponible = iol.estado_cuenta(token)[2]

    # Cotizacion actual de los tickers de las oportunidades y agregarlo al dataframe de oportunidades
    precios = []
    index = []
    cols = ['Cotizacion']
    for ticker in oportunidades.index:
        coti = iol.cotizacion(token, ticker.split('.')[0])
        index.append(ticker)
        precios.append(coti)
    cotizaciones = pd.DataFrame(precios, index=index, columns=cols)
    oportunidades = oportunidades.join(cotizaciones)

    # Toma de decision
    comprado = []
    if oportunidades.count().max() == 0:
        pass
    else:
        if disponible / oportunidades.count().max() >= minimo_inversion:
            for ticker in oportunidades.index:
                precio = round(oportunidades.loc[ticker, 'Cotizacion'] * 1.05, 2)
                cantidad = math.floor(disponible / oportunidades.count().max() / precio)
                compra = iol.trade(token, 'compra', ticker.split('.')[0], cantidad, precio)
                print(compra.status_code)
                print(compra.text)
                comprado.append(ticker)
        else:
            opciones = math.floor(disponible / maximo_inversion)
            oportunidades_bis = oportunidades.copy()
            for i in range(opciones):
                accion = oportunidades_bis['Performance Last 3d'].idxmax()
                precio = round(oportunidades_bis.loc[accion, 'Cotizacion'] * 1.05, 2)
                cantidad = math.floor(disponible / opciones / precio)
                compra = iol.trade(token, 'compra', accion.split('.')[0], cantidad, precio)
                print(compra.status_code)
                print(compra.text)
                comprado.append(accion)
                oportunidades_bis.drop(oportunidades_bis['Performance Last 3d'].idxmax())
    return comprado


def balanceo(token):
    portfolio = iol.portfolio(token)[1]
    portfolio = portfolio[(portfolio['Tipo'] == 'ACCIONES') | (portfolio['Tipo'] == 'CEDEARS')]

    '''ACA HABRIA QUE EVALUAR A CADA ACCION Y VER SI SE LA QUIERE MANTENER EN EL PORTFOLIO O NO.

    PARA ESO HAY QUE EVALUAR EL MACD. SI ES NEGATIVO, SE VENDE.

    TAMBIEN HAY QUE EVALUAR EL PRECIO MAXIMO QUE ALCANZO LA ACCION EN EL PLAZO INVERTIDO Y EVALUAR QUE EL PRECIO
    ACTUAL NO ALCANCE A BAJAR MAS DE UN DETERMINADO PORCENTAJE (PENSAR SI ES UN 10% O EL PRIMER ESCALON DE 
    FIBONACCI, QUE CREO QUE ES 23%)'''
