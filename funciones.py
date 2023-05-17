import pandas as pd
import datetime as dt
import acciones as acc


# MACD 12,26,close,9
# Toma un data frame con la columa del precio al cierre y agrega las 3 columnas del MACD: MACD, Señal e Histograma
def macd(dataframe, column='Adj Close'):
    dataframe['EMA12'] = dataframe[column].ewm(span=12, adjust=False).mean()
    dataframe['EMA26'] = dataframe[column].ewm(span=26, adjust=False).mean()
    dataframe['MACD'] = dataframe['EMA12'] - dataframe['EMA26']
    dataframe['Signal'] = dataframe['MACD'].ewm(span=9, adjust=False).mean()
    dataframe['Histogram'] = dataframe['MACD'] - dataframe['Signal']
    dataframe.drop(['EMA12', 'EMA26'], axis=1, inplace=True)
    return dataframe


# Retornos diarios y de inversion
# A partir de un DF con una columna "Prices" devuelve otro DF con los retornos porcentuales diarios y totales desde el
# principio del DF de origen
def profits(dataframe, column, start_date, end_date=dt.datetime.today()):
    subdf = pd.DataFrame(dataframe.loc[start_date:end_date,column].values, columns=['Prices'], index=dataframe.loc[start_date:end_date].index)
    subdf['Daily Return'] = (subdf['Prices'] / subdf['Prices'].shift(1))-1
    subdf['Return of Investment'] = subdf['Prices'] / subdf['Prices'].iloc[0]
    return subdf


# RSI14
# A partir de un DF con columna de Precios de Cierre, devuelve el mismo DF con una columa adicional con el RSI
def rsi(dataframe, column='Adj Close'):
    dataframe['Daily Return RSI'] = dataframe[column] - dataframe[column].shift(1)
    dataframe['DRpos'] = dataframe['Daily Return RSI'][dataframe['Daily Return RSI']>0]
    dataframe['DRneg'] = - dataframe['Daily Return RSI'][dataframe['Daily Return RSI']<0]
    dataframe['rspos'] = dataframe['DRpos'].rolling(14, min_periods=1).mean()
    dataframe['rsneg'] = dataframe['DRneg'].rolling(14, min_periods=1).mean()
    dataframe['RSI'] = 100 - 100 / (1 + dataframe['rspos'] / dataframe['rsneg'])
    dataframe.drop(['Daily Return RSI','DRpos','DRneg','rspos','rsneg'], axis=1, inplace=True)
    return dataframe


# Sharp Ratio
# >1 es un ratio aceptable, en general
# SR = avg(retorno anual) / desvest(retorno anual)
# Esta funcion toma un DF, una columna y asume un paso diario a menos que se indique lo contrario y devuelve el ratio
# Sharpe
def asr(dataframe, column, paso='d'):
    if paso == 'd':
        sharpe = (252**0.5) * dataframe[column].mean() / dataframe[column].std()
    elif paso == 's':
        sharpe = (52**0.5) * dataframe[column].mean() / dataframe[column].std()
    elif paso == 'm':
        sharpe = (12**0.5) * dataframe[column].mean() / dataframe[column].std()
    elif paso == 'a':
        sharpe = dataframe[column].mean() / dataframe[column].std()
    return sharpe


# Funcion que agrega el maximo y el minimo valor de la columna que se le pase de un dataframe para un gap de tiempo en
# dias especificado
def extremos_locales(df, column='Adj Close', gap=90):
    # Obtengo un subdataframe con fechas de "gap" dias hacia atras. Será la ventana de los máximos y minimos locales
    subdf = df.loc[df.index >= pd.Timestamp(dt.datetime.today().date() - dt.timedelta(days=gap))]
    # Calculo el maximo y minimo locales y los incorporo al subdataframe
    subdf = subdf.assign(LocalMax=subdf[column].max())
    subdf = subdf.assign(LocalMin=subdf[column].min())
    # Devuelvo el dataframe original con el joineo de las dos nuevas columnas, pero solo en las fechas de la ventana
    return df.join(subdf[['LocalMax', 'LocalMin']], how='left')


# Funcion que agrega el máximo y el minimo históricos de la columna que se pase de un dataframe.
def extremos_hist(df, column='Adj Close'):
    return df.assign(AbsMax=df[column].max())


# Funcion que clasifica cada dia usando las columnas de apertura, max, min y cierre del dia
def velas_categ(df, open_price='Open', high='High', low='Low', close='Adj Close'):
    # Calculo la volatilidad como el % que representan la apertura y el cierre respecto de max y min de cada vela
    subdf = pd.DataFrame(abs((df[open_price] - df[close]) / (df[high] - df[low])), columns=['Vela'])
    # Funcion ad-hoc que decide si la volatilidad calculada es alta media o baja
    volat = lambda x: 'Alta' if x <= 0.3 else 'Media' if x < 0.7 else 'Baja'
    # Agrego la columna con la clasificacion de la volatilidad
    subdf['Volatilidad Vela'] = subdf['Vela'].apply(volat)
    # Calculo tambien cuanto representa la max amplitud de la vela respecto del precio, para saber si la Vela es volatil
    # tambien en valores absolutos
    subdf['Amplitud Vela porcent'] = (df[high] - df[low]) / df['Adj Close']
    subdf.drop(['Vela'], axis=1, inplace=True)
    return df.join(subdf, how='left')


# Análisis MACD
def analisis_macd(stocks):
    acciones = []
    data=[]
    cols=['Empresa','Precio','MACD','RSI','Estado RSI', 'Performance Last 3d']
    estado_rsi = ''
    for stock in stocks:
        dataframe = pd.read_csv(f'Stocks Data\\{acc.tickers[stock]}.csv',index_col='Fecha', parse_dates=True)
        df2 = dataframe.loc[dt.datetime.today() - dt.timedelta(days=30):, ['Histogram']]
        df2 = df2[df2['Histogram'] != 0]
        df2['Cambio Signo'] = df2['Histogram'] * df2['Histogram'].shift(1)
        volat = df2['Cambio Signo'][df2['Cambio Signo']<0].count()
        df3 = dataframe.loc[dt.datetime.today() - dt.timedelta(days=15):, ['Histogram']]
        df3 = df3[df3['Histogram'] != 0]
        df3['Cambio Signo'] = df3['Histogram'] * df3['Histogram'].shift(1)
        tarde = df3['Cambio Signo'][df3['Cambio Signo']<0].count()
        df4 = dataframe.loc[dt.datetime.today() - dt.timedelta(days=3):, ['Histogram']]
        df4 = df4[df4['Histogram'] != 0]
        df4['Cambio Signo'] = df4['Histogram'] * df4['Histogram'].shift(1)
        cambio = df4['Cambio Signo'][df4['Cambio Signo'] < 0].count()
        dataframe['Temp'] = (dataframe['Adj Close'] / dataframe['Adj Close'].shift(3)) - 1
        if volat>=1 and volat<=4 and tarde==1 and cambio==1 and dataframe.iloc[-1,8] > 0:
            acciones.append(stock)
            if dataframe.iloc[-1,9] <= 30:
                estado_rsi = 'Sobrevendido'
            elif dataframe.iloc[-1,9] < 50:
                estado_rsi = 'Vendido'
            elif dataframe.iloc[-1,9] < 70:
                estado_rsi = 'Comprado'
            elif dataframe.iloc[-1, 9] >= 70:
                estado_rsi = 'Sobrecomprado'
            data.append([acc.tickers[stock],dataframe.iloc[-1,5],dataframe.iloc[-1,8],dataframe.iloc[-1,9],estado_rsi,dataframe.iloc[-1, 10]])
    oportunidades = pd.DataFrame(data,acciones,cols)
    # oportunidades.rename_axis('Ticker')
    # oportunidades.index.names('Ticker')
    oportunidades.to_csv('Oportunidades.csv',index=True, index_label='Ticker')
    return oportunidades
