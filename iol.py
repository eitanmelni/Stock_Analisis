import requests
import json
import datetime as dt
import os
import pytz
from dateutil import tz
import posiciones as p
import pwinput as pw
import time as tm
import sys


# https://www.youtube.com/watch?v=hNbv1EIUW6g&list=PLpOqH6AE0tNguX5SG8HpcD3lfmzWrIn9n&index=5
# Este modulo gestiona la relacion con Inverir Online. Cada vez que se quiera interactuar con la API para cualquier cosa
# se debe recurrir a alguna funcion dentro de este modulo


def token():
    usr = input("Usuario IOL: ").strip()
    psw = 'Yohimbina.15'  # pw.pwinput('Contraseña IOL: ', '*').strip()

    url = 'https://api.invertironline.com/token'
    args = {'username': usr,
            'password': psw,
            'grant_type': 'password',
            'Content-Type': 'application/x-www-form-urlencoded'
            }
    # Se devuelve el resultado de la funcion que procesa los json de los tokens
    try:
        return process_token_json(requests.post(url, args))
    except:
        print('Usuario y/o Contraseña incorrecto(s)')
        tm.sleep(5)
        sys.exit()


# Funcion que pide user y pass y genera un token nuevo y devuelve la respuesta
def refresh_bearer(refresh_token):
    url = 'https://api.invertironline.com/token'
    args = {'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'Content-Type': 'application/x-www-form-urlencoded'
            }
    # respuesta = requests.post(url, data=args)
    # Se devuelve el resultado de la funcion que procesa los json de los tokens
    return process_token_json(requests.post(url, data=args))


# Funcion que refresca el token de iol llamando con el refresh token registrado en el txt y devuelve la respuesta
# Funcion que se encarga de convertir la respuesta de la API en un diccionario tipo json e interpretar las partes
# relevantes y devolverlas
def process_token_json(respuesta):
    # Se crea un json (diccionario) con la respuesta de la API
    info = json.loads(respuesta.text)
    # Se procesan las fechas de emision y caducidad de la respuesta. Vienen en GMT, entonces las transformo para que se
    # refieran a la zona horaria actual del sistema. Con las 3 fechas se hace lo mismo
    registro_emision = pytz.timezone('GMT').localize(
        dt.datetime.strptime(info['.issued'], '%a, %d %b %Y %H:%M:%S %Z')).astimezone(tz.tzlocal()).replace(tzinfo=None)
    registro_caducidad = pytz.timezone('GMT').localize(
        dt.datetime.strptime(info['.expires'], '%a, %d %b %Y %H:%M:%S %Z')).astimezone(tz.tzlocal()).replace(
        tzinfo=None)
    registro_caducidad_refresh = pytz.timezone('GMT').localize(
        dt.datetime.strptime(info['.refreshexpires'], '%a, %d %b %Y %H:%M:%S %Z')).astimezone(tz.tzlocal()).replace(
        tzinfo=None)
    # Se devuelve una lista de strings con el codigo de respuesta, los dos token y las 3 fechas relevantes
    return [respuesta,
            info['access_token'],
            info['refresh_token'],
            registro_emision,
            registro_caducidad,
            registro_caducidad_refresh]


# Funcion para generar y almacenar la info de un nuevo token
def registro_token(refresh=False):
    if refresh:
        with open('token.txt', 'r') as archivo_token:
            # Leer cada línea del archivo y guardarla en una lista
            lineas = archivo_token.readlines()
        # Genero un token de IOL
        token_iol = refresh_bearer(lineas[2].strip())
    else:
        # Genero un token de IOL
        token_iol = token()

    # Guardo en un csv la info relevante: codigo de salida, los 2 tokens, fecha de emision y fechas de caducidad
    with open('token.txt', 'w') as archivo:
        # Escribir cada elemento de la lista en una línea separada del archivo
        archivo.writelines("%s\n" % elemento for elemento in token_iol)


# Funcion que tiene como objetivo chequear si el token existe y sigue vigente. Si no es asi, genera uno nuevo y devuelve
# el valor para hacer la siguiente consulta por API
def gestor_token():
    # Chequeo si el archivo de token existe. Si no existe, hay que crear un token y luego almacenarlo en un txt
    if 'token.txt' not in os.listdir('.'):
        registro_token(refresh=False)
    # Si existe ya un file, hay que verificar su contenido y las fechas asentadas en el
    else:
        # Abrir el archivo en modo de lectura (que ya existia o fue creado recien)
        with open('token.txt', 'r') as archivo_token:
            # Leer cada línea del archivo y guardarla en una lista
            lineas = archivo_token.readlines()

        # Chequeo si caduco la posibilidad de refrescar el token
        if dt.datetime.today() > dt.datetime.strptime(lineas[5].strip(), '%Y-%m-%d %H:%M:%S'):
            registro_token(refresh=False)
        # Si es necesario refrescar el token, debido a que ya caduco pero aun se puede refrescar, se hace el refresh
        elif dt.datetime.today() > dt.datetime.strptime(lineas[4].strip(), '%Y-%m-%d %H:%M:%S'):
            registro_token(refresh=True)

    with open('token.txt', 'r') as archivo_token:
        # Leer cada línea del archivo y guardarla en una lista
        lineas = archivo_token.readlines()
    return lineas[1].strip()


def serie_hist(stock, token, start='2022-01-01', end=dt.datetime.today().date(), mercado='bCBA'):
    url = f'https://api.invertironline.com///api/v2/{mercado}/Titulos/{stock}/Cotizacion/seriehistorica/{start}/{end}/ajustada'
    headers = {'Accept': 'application/json',
               'Authorization': f'Bearer {token}'
               }
    # Devuelve el json (y la metadata) en respuesta al llamado de la API
    return requests.get(url=url, headers=headers)


def estado_cuenta(token):
    url = 'https://api.invertironline.com//api/v2/estadocuenta'
    headers = {'Accept': 'application/json',
               'Authorization': f'Bearer {token}'
               }
    cuenta = requests.get(url=url, headers=headers)
    respuesta = json.loads(cuenta.text)
    invertido = respuesta['cuentas'][0]['titulosValorizados']
    disponible = respuesta['cuentas'][0]['disponible']  # + respuesta['cuentas'][0]['comprometido']
    total = respuesta['cuentas'][0]['total']
    # reservado_imp = invertido * 0.006
    # disponible = disponible - reservado_imp
    return [disponible, invertido, total, cuenta]


def operaciones(token, desde=None, hasta=dt.datetime.today()):
    # Seteo de la consulta a la API
    url = 'https://api.invertironline.com//api/v2/operaciones'
    headers = {'Accept': 'application/json',
               'Authorization': f'Bearer {token}'
               }
    args = {
        'filtro.estado': 'terminadas',
        # 'filtro.numero': numero,
        'filtro.fechaDesde': desde,
        'filtro.fechaHasta': hasta
        # , 'filtro.pais': pais
    }
    # Ejecucion de la consulta y guardado de respuesta
    respuesta = requests.get(url=url, headers=headers, params=args)
    # Inicializo la lista de operaciones y vamos acomodando en orden las operaciones en la lista, filtrando los bonos
    # de dolar bolsa
    opers = []
    for oper in json.loads(respuesta.text):
        if oper['simbolo'] not in ['AL30D', 'AL30']:
            opers.append(oper)
    # Devuelvo la lista de jsons de operaciones
    return opers


def cotizacion(token, simbolo, mercado='bCBA', plazo='t2'):
    url = f'https://api.invertironline.com//api/v2/{mercado}/Titulos/{simbolo}/Cotizacion'
    headers = {'Accept': 'application/json',
               'Authorization': f'Bearer {token}'
               }
    args = {
        'model.mercado': mercado,
        'model.simbolo': simbolo,
        'model.plazo': plazo
    }
    cotizacion = requests.get(url=url, headers=headers, params=args)
    ultimo_precio = json.loads(cotizacion.text)['ultimoPrecio']
    return ultimo_precio


# LIMITE DE LO CHEQUEADO
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def portfolio(token):
    url = 'https://api.invertironline.com//api/v2/portafolio/argentina'
    args = {'api_key': token}
    headers = {'Accept': 'application/json',
               'Authorization': f'Bearer {token}'
               }
    respuesta = requests.get(url=url, params=args, headers=headers)
    posiciones = []
    if respuesta.status_code == 200:
        for activo in json.loads(respuesta.text)['activos']:
            posiciones.append(p.Posicion(ticker=activo['titulo']['simbolo'],
                                         fecha_c=dt.datetime.today(),
                                         precio_c=activo['ppc'],
                                         cantidad_titulos=activo['cantidad'],
                                         precio_v=activo['ultimoPrecio']
                                         )
                              )
    return posiciones


def trade(token, operacion, ticker, cantidad, precio, plazo='t0'):
    url = f'https://api.invertironline.com//api/v2/operar/{operacion.title()}'
    headers = {'Accept': 'application/json',
               'Authorization': f'Bearer {token}'
               }
    args = {
        'mercado': 'bCBA',
        'simbolo': ticker,
        'cantidad': cantidad,
        'precio': precio,
        'plazo': plazo,
        'validez': dt.datetime.today() + dt.timedelta(days=1)
    }
    cuenta = requests.post(url=url, headers=headers, data=args)
    return cuenta
