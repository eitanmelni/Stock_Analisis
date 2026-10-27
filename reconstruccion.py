from pandas import DataFrame, Series, Timestamp, Timedelta, read_csv
from pandas.tseries.offsets import MonthEnd
from datetime import datetime
from json import loads
from os import listdir, mkdir, path
from unicodedata import normalize
import logging
import iol

# Este modulo reconstruye hacia atras la evolucion de la cartera, con un punto por mes, desde el ultimo momento en que no
# se tenia ninguna accion. El valor de la cartera es titulos + cash. El cash se arma con las compras y ventas (que vienen
# de IOL) y con los movimientos de plata que no son operaciones (depositos, retiros, dividendos, comisiones...), que se
# cargan a mano en un csv porque no encontre forma de obtenerlos por API. Solo los depositos y retiros se consideran
# aportes externos para la TIR: los dividendos, rentas, intereses y comisiones son resultado de la cartera.
ARCHIVO_HISTORIA = 'Seguimiento/historia_cartera.csv'
ARCHIVO_MOVIMIENTOS = 'Seguimiento/movimientos_cash.csv'
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


def _sin_tildes(texto):
    return normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode().strip().lower()


# Lee el csv de movimientos de cash que no son operaciones. Columnas: Fecha (AAAA-MM-DD), Tipo y Monto. Los tipos
# 'Deposito' y 'Retiro' son aportes externos (el signo del monto se corrige solo: deposito suma y retiro resta). Un tipo
# 'Saldo Inicial' es el cash que ya habia el dia que empieza la tenencia continua (cuenta como un deposito ese dia).
# Cualquier otro tipo (Dividendo, Renta, Comision, Impuesto, Interes...) se toma con el signo del monto y es resultado
def leer_movimientos(path_f=ARCHIVO_MOVIMIENTOS):
    cols = ['Fecha', 'Tipo', 'Monto']
    if not path.exists(path_f):
        return DataFrame(columns=cols)
    df = read_csv(path_f, parse_dates=['Fecha'])[cols]
    df['Fecha'] = df['Fecha'].dt.normalize()
    return df.sort_values('Fecha', kind='stable').reset_index(drop=True)


# Devuelve para un movimiento (Tipo, Monto) si es un aporte externo y su monto con el signo correcto
def clasificar_movimiento(tipo, monto):
    t = _sin_tildes(tipo)
    if t.startswith('deposito') or t == 'saldo inicial':
        return True, abs(monto)
    if t.startswith('retiro'):
        return True, -abs(monto)
    return False, monto


# Arma la historia de la cartera: un renglon por punto con el valor total (titulos + cash), lo aportado neto por depositos
# y retiros, el resultado, la TIR y el valor de cada papel. precios es un diccionario {ticker: Series de cierres indexada
# por fecha} y movs es el dataframe que devuelve leer_movimientos. Los movimientos anteriores al inicio se ignoran: lo que
# haya de cash a esa fecha debe estar en un movimiento 'Saldo Inicial'
def construir_historia(ops, precios, movs, hoy):
    inicio = inicio_tenencia_continua(ops)
    ops = ops[ops['Fecha'] >= inicio].copy()
    ops['Flujo'] = ops.apply(lambda f: -f.Cantidad * f.Precio if f.Tipo == 'Compra' else f.Cantidad * f.Precio, axis=1)
    ops['CantFirmada'] = ops.apply(lambda f: f.Cantidad if f.Tipo == 'Compra' else -f.Cantidad, axis=1)
    tickers = sorted(ops['Ticker'].unique())

    # Movimientos de cash desde el inicio, con su clasificacion. El saldo inicial se ubica en la fecha de inicio
    filas_mov = []
    for m in movs.itertuples():
        es_saldo_inicial = _sin_tildes(m.Tipo) == 'saldo inicial'
        if m.Fecha >= inicio or es_saldo_inicial:
            externo, monto = clasificar_movimiento(m.Tipo, m.Monto)
            filas_mov.append([inicio if es_saldo_inicial else m.Fecha, externo, monto])
    mov = DataFrame(filas_mov, columns=['Fecha', 'Externo', 'Monto']).astype({'Externo': bool, 'Monto': float})

    filas = []
    for fecha in puntos_mensuales(inicio, Timestamp(hoy).normalize()):
        # Todo lo operado y movido hasta el final de ese dia
        hasta = ops[ops['Fecha'] < fecha + Timedelta(days=1)]
        mov_hasta = mov[mov['Fecha'] < fecha + Timedelta(days=1)]
        cantidades = hasta.groupby('Ticker')['CantFirmada'].sum()
        valores = {}
        for tk in tickers:
            cant = cantidades.get(tk, 0)
            valores[tk] = round(cant * precio_a_fecha(tk, fecha, precios, ops), 2) if round(cant, 6) != 0 else 0.0
        titulos = sum(valores.values())
        cash = hasta['Flujo'].sum() + mov_hasta['Monto'].sum()
        if cash < -0.01:
            logging.warning(f'Cash negativo al {fecha.date()}: {cash:.2f}. Faltan depositos o saldo inicial en movimientos')
        total = titulos + cash

        # Para la TIR solo cuentan como flujos los aportes externos. Un deposito es plata que el inversor pone (negativo)
        externos = mov_hasta[mov_hasta['Externo']]
        flujos = [(f.Fecha, -f.Monto) for f in externos.itertuples()] + [(fecha, total)]
        aportes = externos['Monto'].sum()
        tir = xirr(flujos)
        filas.append({'Fecha': fecha.date(), 'Valor Total': round(total, 2), 'Valor Titulos': round(titulos, 2),
                      'Cash': round(cash, 2), 'Aportes Netos Acumulados': round(aportes, 2),
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
    crudas = iol.operaciones(token, DESDE_OPERACIONES)
    ignoradas = sorted({o['tipo'] for o in crudas if o['tipo'] not in ['Compra', 'Venta']})
    if ignoradas:
        print(f'- Tipos de operacion ignorados (no son compra ni venta): {ignoradas}')
    ops = normalizar_operaciones(crudas)
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

    movs = leer_movimientos()
    if len(movs) == 0:
        print(f'- ATENCION: no hay movimientos de cash en {ARCHIVO_MOVIMIENTOS}. Sin depositos el cash y la TIR no son confiables')
    df = construir_historia(ops, precios, movs, hoy)
    if 'Seguimiento' not in listdir('.'):
        mkdir('Seguimiento')
    df.to_csv(path_f, index=False)
    print(f'- Historia guardada en {path_f} ({len(df)} puntos)')

    # Contraste con el estado de cuenta real de hoy. Si no coincide, faltan movimientos o hay un problema de precios
    try:
        disponible, invertido, _, _ = iol.estado_cuenta(iol.gestor_token())
        print(f'- Control contra IOL hoy: titulos reconstruidos {df["Valor Titulos"].iloc[-1]:,.2f} vs {invertido:,.2f} '
              f'| cash reconstruido {df["Cash"].iloc[-1]:,.2f} vs {disponible:,.2f}')
    except Exception:
        logging.error('No se pudo contrastar contra el estado de cuenta de IOL')
        print('- No se pudo contrastar contra el estado de cuenta de IOL')
    return df


if __name__ == '__main__':
    logging.basicConfig(filename='Logs/reconstruccion.log', filemode='w', encoding='utf-8', level=logging.INFO,
                        format='%(levelname)s - %(asctime)s - %(filename)s, %(funcName)s, line%(lineno)d: %(message)s',
                        datefmt='%H:%M:%S')
    reconstruir_historia()
