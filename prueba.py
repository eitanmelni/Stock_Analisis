import datetime as dt
import posiciones as p
import portfolios as pf
import pandas as pd
import iol
import logs
import os
import matplotlib.pyplot as plt
import requests
import json
import graficos as gr


'''token = iol.gestor_token()
print(token)
cuenta = iol.estado_cuenta(token)
port1 = pf.Portfolio(cuenta[0])
print(port1)
port1.agregar_pos(iol.operaciones_iniciacion(token, dt.datetime(2023, 3, 1)))
print(port1)
print(port1.registro_port())
pf.bajar_portfolio(port1)'''

'''path='Seguimiento/ultimo_portfolio.csv'
# Busco el archivo del ultimo portfolio
df = pd.read_csv(path, index_col='#')
df = df.drop(0).reset_index(drop=True)
print(dt.datetime.strptime(df.loc[0]['Fecha Compra'], '%Y-%m-%dT%H:%M:%S.%f').date())'''

'''acc = [['a', 2], ['b', 5], ['c', 6], ['a', 4]]
rem = ['d', 7]
n = len(acc)
i = 0
print(acc)
while i in range(n) and rem[1] > 0:
    if acc[i][0] == rem[0]:
        if rem[1] >= acc[i][1]:
            rem[1] -= acc[i][1]
            acc.remove(acc[i])
            n -= 1
        else:
            acc[i][1] -= rem[1]
            rem[1] = 0
    else:
        i += 1
print(acc)'''



pos1 = p.Posicion('ALUA', dt.datetime(2023, 1, 1), 100, 3, 'Cerrada', dt.datetime(2023, 1, 4), 117)
pos3 = p.Posicion('MELI', dt.datetime(2023, 1, 1), 130, 4)
pos2 = p.Posicion('BABA', dt.datetime(2023, 1, 1), 1000, 30, 'Abierta', dt.datetime(2023, 2, 4), 1231.7)
pos4 = p.Posicion('GGAL', dt.datetime(2023, 1, 1), 3000, 13)
pos5 = p.Posicion('YPFD', dt.datetime(2023, 1, 1), 2340, 5)
pos6 = p.Posicion('C', dt.datetime(2023, 1, 1), 2340, 5)
pos7 = p.Posicion('BMA', dt.datetime(2023, 1, 1), 2340, 5)
pos8 = p.Posicion('COME', dt.datetime(2023, 1, 1), 2340, 5)

pos = [pos1, pos2, pos3, pos4, pos5, pos6, pos7, pos8]

port1 = pf.Portfolio(600)

port1.agregar_pos(pos)

print(port1)

valores = [port1.cash()]
etiquetas = ['Disponible']
rendimientos = [0]

for pos in port1.posiciones():
    valores.append(pos.valor())
    etiquetas.append(pos.nombre())
    rendimientos.append(pos.rendimiento())

# Calculo el total de la cartera y creo una lista con los porcentajes
total = sum(valores)
porcentajes = [valor / total for valor in valores]

# Armo un Dataframe temporal para ordenar las acciones como mejor se pueda de forma de no superponer etiquetas
cols = ['Acc', 'Valor', 'Rend', 'Share']
info_graf = pd.DataFrame(data=[etiquetas, valores, rendimientos, porcentajes], index=cols)
info_graf = info_graf.transpose().sort_values(by='Share', ignore_index=True)
info_graf['Bool'] = info_graf['Share'].apply(lambda x: x < 0.05)

# Cuento cantidad de acciones de mas y menos de 5% de share
chicas = sum(info_graf['Bool'])
todas = len(info_graf)
# Defino cuales de las acciones chicas se deben intercambiar para no solapar etiquetas (tengo sus filas en el DF)
chicas_inter = [elem for elem in range(chicas) if elem % 2 == 1]
# Defino cuales de las acciones grandes se pueden intercambiar (tengo sus filas en el DF)
grandes_inter = [elem for elem in range(chicas, todas) if elem % 2 == todas % 2 and elem != chicas]

# Se toma el minimo entre las dos cantidades a intercambiar y se corta la lista mas grande
if len(chicas_inter) > len(grandes_inter):
    chicas_inter = list(chicas_inter[:len(grandes_inter)])
else:
    grandes_inter = list(grandes_inter[:len(chicas_inter)])

# Se hacen los intercambios de filas que se pueden hacer
for i in range(len(chicas_inter)):
    info_graf.loc[[chicas_inter[i], grandes_inter[i]]] = info_graf.loc[[grandes_inter[i], chicas_inter[i]]].values

# Hay que separar de nuevo el DF en las listas originales, ahora ordenadas convenientemente
etiquetas = list(info_graf['Acc'])
valores = list(info_graf['Valor'])
rendimientos = list(info_graf['Rend'])

print(info_graf)
print()
print(etiquetas)
print(valores)
print(rendimientos)

'''log_info = dict()
log_info['ultima_actu_portfolio'] = '2023-04-15 18:03:45'
log_info['ultima_actu_historico'] = '2023-04-16 15:03:45'


logs.actualizar_log(log_info)'''

# Prueba ACTUALIZAR PORTFOLIO
'''log_info = logs.buscar_log()
print(log_info)

pos1 = p.Posicion('ALUA', dt.datetime(2023, 1, 1), 190, 180)
pos2 = p.Posicion('MELI', dt.datetime(2023, 1, 1), 1000, 30)


pos = [pos1, pos2]

port1 = pf.Portfolio(60000)

port1.agregar_pos(pos)

print(port1)

port1.actualizar_portfolio(log_entry='ultima_actu_portfolio', guarda_cerradas=True)

print(port1)'''


# PRUEBA TOMA GANANCIAS
'''pos1 = p.Posicion('ALUA', dt.datetime(2023, 1, 1), 190, 180)
print(pos1)

pos2 = pos1.toma_ganancia(100, dt.datetime(2023, 1, 1), 191)
print(pos1)
print(pos2)
'''

# PRUEBA ACTUALIZAR PORTFOLIO
'''#ultimo_port = pf.levantar_portfolio('Seguimiento/ultimo_portfolio.csv')
ultimo_port = pf.levantar_portfolio('Seguimiento/ultimo_historico.csv')

#ultimo_port.actualizar_portfolio(log_entry='ultima_actu_portfolio', guarda_cerradas=False)
ultimo_port.actualizar_portfolio(log_entry='ultima_actu_historico', guarda_cerradas=True)

#pf.bajar_portfolio(ultimo_port, 'Seguimiento/ultimo_portfolio.csv')
pf.bajar_portfolio(ultimo_port, 'Seguimiento/ultimo_historico.csv')
print(ultimo_port)'''


# PRUEBA DE IOL.OPERACIONES
'''log_entry = 'ultima_actu_portfolio'

token = iol.gestor_token()
# Busco la info del log y saco el tiempo relevante del json
log_info = logs.buscar_log()
timestamp = dt.datetime.strptime(log_info[log_entry], '%Y-%m-%d %H:%M:%S.%f')
# Traigo las operaciones desde el dia de ese timestamp
operaciones = iol.operaciones(token, timestamp.date())
print(operaciones)'''
