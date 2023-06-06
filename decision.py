from pandas import DataFrame, Timestamp, read_csv
import math
import acciones as acc
import funciones as fs
import iol


def oportunidad_compra(dataframe: DataFrame):
    dataframe['macd anterior'] = dataframe['MACD'].shift(1)
    dataframe['cambio macd'] = (dataframe['MACD'] * dataframe['macd_anterior'] < 0)


'''
¿Como tomar las decisiones?
Compra:
- MACD y RSI
'''


'''
TENDENCIAS: 
- Definicion: una tendencia alcista esta marcada por minimos crecientes. Una tendencia bajista esta marcada por maximos
decrecientes.
- Dos formas de identificar tendencias: Identificar maximos y minimos locales y comparar el precio con una media movil

Identificar maximos y minimos locales:
- Revisar, para cada punto de la serie historica de una accion, el contexto de precios de los x dias posteriores y 
anteriores para identifcar los máximos y minimos locales. Se tiene un maximo o minimo local siempre y cuando en el 
contexto de puntos que se está revisando ese punto sea un maximo o minimo y no este situado en los bordes del intervalo
(lo cual no puede suceder porque estoy tomando puntos que tienen contexto).
- Una vez que se tienen los maximos y minimos locales, hay que empezar a compararlos entre si y ver si hay muchos 
minimos crecientes seguidos o muchos maximos decrecientes seguidos. 

Media Movil:
- Elegir un plazo para la media movil. En el momento en que el precio se corta con la media movil, el precio puede estar
cambiando de tendencia. 
'''
