from pandas import DataFrame, Series, Timestamp, Timedelta
from pandas.tseries.offsets import MonthEnd
from datetime import datetime
from json import loads
from os import listdir, mkdir
import logging
import iol

# Este modulo reconstruye hacia atras la evolucion de la cartera de titulos, con un punto por mes, desde el ultimo momento
# en que no se tenia ninguna accion. Se usan solo los titulos: cada compra es plata que entra a la cartera y cada venta es
# plata que sale, asi que no hace falta conocer depositos ni retiros de la cuenta.
ARCHIVO_HISTORIA = 'Seguimiento/historia_cartera.csv'
DESDE_OPERACIONES = '2015-01-01'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CALCULO (no depende de IOL)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Devuelve el dataframe de operaciones (solo compras y ventas) ordenado por fecha y hora, con las columnas Fecha, Ticker,
# Tipo, Cantidad y Precio, a partir de la lista de jsons que devuelve iol.operaciones
def normalizar_operaciones(opers):
    filas = []
    for oper in opers:
        if oper['tipo'] in ['Compra', 'Venta']:
            filas.append([datetime.strptime(oper['fechaOperada'].split('.')[0], '%Y-%m-%dT%H:%M:%S'),
                          oper['simbolo'], oper['tipo'], oper['cantidadOperada'], oper['precioOperado']])
        else:
            logging.warning(f'Operacion ignorada por tipo no contemplado: {oper["tipo"]} {oper["simbolo"]}')
    df = DataFrame(filas, columns=['Fecha', 'Ticker', 'Tipo', 'Cantidad', 'Precio'])
    return df.sort_values('Fecha', kind='stable').reset_index(drop=True)


# Busca la fecha de la primera operacion de la ultima tenencia continua, es decir, la primera compra posterior al ultimo
# momento en que la cantidad de titulos de la cartera fue cero. Si nunca llego a cero, es la primera operacion
def inicio_tenencia_continua(ops):
    tenencia = {}
    inicio = None
    for fila in ops.itertuples():
        # Si la cartera estaba vacia, esta operacion abre una nueva tenencia continua
        if all(round(c, 6) == 0 for c in tenencia.values()):
            inicio = fila.Fecha
        signo = 1 if fila.Tipo == 'Compra' else -1
        tenencia[fila.Ticker] = tenencia.get(fila.Ticker, 0) + signo * fila.Cantidad
    return inicio.normalize()


# Fechas de los puntos de la serie: el dia de inicio, cada fin de mes intermedio y el dia de hoy
def puntos_mensuales(inicio, hoy):
    fechas = [inicio]
    fin_mes = inicio + MonthEnd(0)
    while fin_mes < hoy:
        if fin_mes > inicio:
            fechas.append(fin_mes)
        fin_mes = fin_mes + MonthEnd(1)
    if hoy > inicio:
        fechas.append(hoy)
    return fechas


# TIR anualizada (efectiva) de una lista de flujos (fecha, monto) por biseccion. Devuelve None si no tiene solucion, por
# ejemplo si todos los flujos tienen el mismo signo o si todo ocurre el mismo dia
def xirr(flujos):
    if len(flujos) < 2 or min(m for _, m in flujos) >= 0 or max(m for _, m in flujos) <= 0:
        return None
    t0 = min(f for f, _ in flujos)
    if max(f for f, _ in flujos) == t0:
        return None

    def vpn(tasa):
        return sum(m / (1 + tasa) ** ((f - t0).days / 365) for f, m in flujos)

    bajo, alto = -0.999999, 1000.0
    if vpn(bajo) * vpn(alto) > 0:
        return None
    for _ in range(300):
        medio = (bajo + alto) / 2
        if vpn(bajo) * vpn(medio) <= 0:
            alto = medio
        else:
            bajo = medio
    return (bajo + alto) / 2


# Precio de un papel a una fecha: ultimo cierre disponible hasta ese dia en la serie historica. Si la serie no tiene datos
# hasta esa fecha, se usa el precio de la ultima operacion propia hasta ese dia (y se avisa)
def precio_a_fecha(ticker, fecha, precios, ops):
    serie = precios.get(ticker)
    if serie is not None and len(serie) > 0 and serie.index[0] <= fecha:
        return float(serie.asof(fecha))
    previas = ops[(ops['Ticker'] == ticker) & (ops['Fecha'] < fecha + Timedelta(days=1))]
    logging.warning(f'Sin serie historica de {ticker} al {fecha.date()}: se usa el precio de la ultima operacion')
    return float(previas['Precio'].iloc[-1])


# Arma la historia de la cartera: un renglon por punto con el valor total, lo aportado neto, el resultado, la TIR y el
# valor de cada papel. precios es un diccionario {ticker: Series de cierres indexada por fecha}
def construir_historia(ops, precios, hoy):
    inicio = inicio_tenencia_continua(ops)
    ops = ops[ops['Fecha'] >= inicio].copy()
    ops['Flujo'] = ops.apply(lambda f: -f.Cantidad * f.Precio if f.Tipo == 'Compra' else f.Cantidad * f.Precio, axis=1)
    ops['CantFirmada'] = ops.apply(lambda f: f.Cantidad if f.Tipo == 'Compra' else -f.Cantidad, axis=1)
    tickers = sorted(ops['Ticker'].unique())

    filas = []
    for fecha in puntos_mensuales(inicio, Timestamp(hoy).normalize()):
        # Todo lo operado hasta el final de ese dia
        hasta = ops[ops['Fecha'] < fecha + Timedelta(days=1)]
        cantidades = hasta.groupby('Ticker')['CantFirmada'].sum()
        valores = {}
        for tk in tickers:
            cant = cantidades.get(tk, 0)
            valores[tk] = round(cant * precio_a_fecha(tk, fecha, precios, ops), 2) if round(cant, 6) != 0 else 0.0
        total = sum(valores.values())
        flujos = [(f.Fecha.normalize(), f.Flujo) for f in hasta.itertuples()] + [(fecha, total)]
        aportes = -hasta['Flujo'].sum()
        tir = xirr(flujos)
        filas.append({'Fecha': fecha.date(), 'Valor Total': round(total, 2),
                      'Aportes Netos Acumulados': round(aportes, 2),
                      'Resultado Nominal': round(total - aportes, 2),
                      'TIR Anualizada': None if tir is None else round(tir, 6),
                      **valores})
    return DataFrame(filas)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DESCARGA DE DATOS DE IOL
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Baja la serie historica de cierres de un papel desde la fecha indicada. Devuelve None si la descarga falla
def serie_cierres(ticker, token, desde, hasta):
    resp = iol.serie_hist(ticker, token, desde, hasta)
    if resp.status_code not in [200, 201]:
        logging.warning(f'Serie historica de {ticker} fallida: codigo {resp.status_code}')
        return None
    datos = loads(resp.text)
    if len(datos) == 0:
        return None
    serie = Series({Timestamp(d['fechaHora'].split('T')[0]): d['ultimoPrecio'] for d in datos})
    return serie.sort_index()


def reconstruir_historia(path_f=ARCHIVO_HISTORIA):
    logging.info('Comienza la reconstruccion de la historia de la cartera')
    token = iol.gestor_token()
    ops = normalizar_operaciones(iol.operaciones(token, DESDE_OPERACIONES))
    if len(ops) == 0:
        raise ValueError('IOL no devolvio operaciones de compra o venta')
    inicio = inicio_tenencia_continua(ops)
    print(f'- Operaciones encontradas: {len(ops)}. La tenencia continua actual empieza el {inicio.date()}')

    hoy = datetime.today().date()
    desde = (inicio - Timedelta(days=10)).date()
    precios = {}
    for tk in sorted(ops[ops['Fecha'] >= inicio]['Ticker'].unique()):
        token = iol.gestor_token()
        precios[tk] = serie_cierres(tk, token, desde, hoy)
        print(f'- {tk}: {"ok" if precios[tk] is not None else "sin serie historica (se usara el precio de tus operaciones)"}')

    df = construir_historia(ops, precios, hoy)
    if 'Seguimiento' not in listdir('.'):
        mkdir('Seguimiento')
    df.to_csv(path_f, index=False)
    print(f'- Historia guardada en {path_f} ({len(df)} puntos)')
    return df


if __name__ == '__main__':
    logging.basicConfig(filename='Logs/reconstruccion.log', filemode='w', encoding='utf-8', level=logging.INFO,
                        format='%(levelname)s - %(asctime)s - %(filename)s, %(funcName)s, line%(lineno)d: %(message)s',
                        datefmt='%H:%M:%S')
    reconstruir_historia()
