import pandas as pd
import datetime as dt
import os
import iol
import logs
import posiciones as p


class Portfolio:
    def __init__(self, cash=0):
        self._cash_disp = cash
        self._posiciones = []

    def __str__(self):
        repres = ['--------------- Portfolio ---------------',
                  f'Dinero Disponible: ${self.cash():.2f}', '\nPosiciones:',
                  ' | '.join([f'{"Accion":^35}', f'{"Valor":^30}', f'{"Rendimiento":^30}', f'{"Tasa Mensualizada":^20}', f'{"Estado":^10}']),
                  ' | '.join([f'{"":-<35}', f'{"":->30}', f'{"":->30}', f'{"":->20}', f'{"":->10}'])]
        for pos in self.posiciones():
            col1 = f'{pos.ticker()} ({pos.nombre()})'
            col2 = f'${pos.valor():.2f} ({pos.cantidad():.0f} x ${pos.precio_venta():.2f})'
            col3 = f'{pos.rendimiento():.2%} en {(pos.fecha_venta()-pos.fecha_compra())/dt.timedelta(days=1):.0f} dias'
            # Le sumo 1 a la longitud de la posicion para evitar dividir por cero
            col4 = f'{(1 + pos.rendimiento()) ** (30 / (len(pos) + 1)) - 1:.2%}'
            col5 = f'{pos.estado()}'
            repres.append(' | '.join([f'{col1:<35}', f'{col2:>30}', f'{col3:>30}', f'{col4:^20}', f'{col5:^10}']))
        return '\n'.join(repres)

    def cash(self):
        return self._cash_disp

    def posiciones(self):
        return self._posiciones

    def modif_cash(self, cash_nuevo):
        self._cash_disp = cash_nuevo

    def ordenar(self):
        self._posiciones.sort()

    # Genera el registro del portfolio en forma de un dataframe
    def registro_port(self):
        cols = ['Ticker', 'Fecha Compra', 'Precio Compra', 'Cantidad', 'Estado', 'Fecha Venta', 'Precio Venta',
                'Valor', 'Rendimiento', 'Renidmiento Mensualizado']
        data = [['CASH', '', '', '', '', '', '', self._cash_disp, '', '']]
        for posicion in self._posiciones:
            data.append(posicion.registro())
        return pd.DataFrame(data=data, columns=cols)

    # Agrega una lista de posiciones a la que ya tiene
    def agregar_pos(self, posiciones):
        self._posiciones += posiciones

    # Remueve una lista de posiciones a la que ya tiene
    def remover_pos(self, tickr, cant, guarda_cerradas=False, precio=None, fecha=None):
        # Inicializo el tamaño de la lista de posiciones y el contador i
        n = len(self._posiciones)
        i = 0
        # El loop sigue siempre y cuando no se haya recorrido toda la lista o que la cantidad de acciones para descontar
        # sea cero
        while i in range(n) and cant > 0:
            if self._posiciones[i].ticker() == tickr:
                # Para el ticker correcto se descuenta la cantidad de acciones que se puede de las posiciones y se
                # descuenta el mismo numero del parametro cant de la funcion, es decir que esas son las acciones que
                # aun falta descontar del portfolio
                if cant >= self._posiciones[i].cantidad():
                    cant -= self._posiciones[i].cantidad()
                    if not guarda_cerradas:
                        self._posiciones.remove(self._posiciones[i])
                        n -= 1
                    else:
                        self._posiciones[i].modif_precio(precio)
                        self._posiciones[i].modif_estado('Cerrada')
                        self._posiciones[i].modif_fecha(fecha)
                        self._posiciones[i].recalcular()
                        i += i
                else:
                    self._posiciones.append(self._posiciones[i].toma_ganancia(cant, fecha, precio))
                    cant = 0
            else:
                i += 1

    # Las funciones de agrandar_pos y achicar_pos parecen no ser necesarias por el momento, ya que cada posicion que se
    # sume no va a importar si ya habia una posicion abierta para ese mismo papel. Puede haber muchas posiciones del
    # mismo papel abiertas al mismo tiempo
    '''# Profundiza la posicion en un activo determinado
    def agrandar_pos(self):
        pass

    # Achica la posicion en un activo determinado
    def achicar_pos(self):
        pass'''

    # Metodo que pide a la API la operaciones desde la ultima fecha en que se consultaron
    def actualizar_portfolio(self, log_entry, guarda_cerradas=False):
        # Traigo/Genero token
        token = iol.gestor_token()
        # Busco la info del log y saco el tiempo relevante del json
        log_info = logs.buscar_log()
        # Si no existe log_info, se asume que es la primera vez que se corre el script y se va a buscar el portf actual
        if log_info == dict():
            # Busco el estado de cuenta para modificar el cash y el portfolio actual para traer la lista de posiciones
            self.modif_cash(iol.estado_cuenta(token)[0])
            self.agregar_pos(iol.portfolio(token))
        else:
            timestamp = dt.datetime.strptime(log_info[log_entry], '%Y-%m-%d %H:%M:%S.%f')
            # Traigo las operaciones desde el dia de ese timestamp
            operaciones = iol.operaciones(token, timestamp.date())
            operaciones.reverse()
            # Filtro las transacciones solamente posteriores a la hora del timestamp
            opers = []
            for oper in operaciones:
                if dt.datetime.strptime(oper['fechaOperada'].split('.')[0], '%Y-%m-%dT%H:%M:%S') > timestamp:
                    opers.append(oper)
            # Tengo en opers las operaciones a actualizar verdaderamente. Se actualizan en el portfolio indicado
            for oper in opers:
                if oper['tipo'] == 'Venta':
                    self.remover_pos(oper['simbolo'],
                                     oper['cantidadOperada'],
                                     guarda_cerradas,
                                     oper['precioOperado'],
                                     dt.datetime.strptime(oper['fechaOperada'], '%Y-%m-%dT%H:%M:%S'))
                elif oper['tipo'] == 'Compra':
                    nueva_pos = p.Posicion(oper['simbolo'],
                                           dt.datetime.strptime(oper['fechaOperada'].split('.')[0],
                                                                '%Y-%m-%dT%H:%M:%S').date(),
                                           oper['precioOperado'],
                                           oper['cantidadOperada'])
                    self.agregar_pos([nueva_pos])
        self.ordenar()
        log_info[log_entry] = dt.datetime.strftime(dt.datetime.today(), '%Y-%m-%d %H:%M:%S.%f')
        logs.actualizar_log(log_info)

    def actualizar_precios(self, cambiar_cash=True):
        # Traigo/Genero token
        token = iol.gestor_token()
        # Cambio el dinero disponible en el portfolio
        if cambiar_cash:
            # Traigo el dinero disponible y lo modifico en el portfolio
            self.modif_cash(iol.estado_cuenta(token)[0])
        # Para cada posicion en el port, busco su ultimo precio y la modifico. Modifico tambien la fecha por la actual
        for pos in self.posiciones():
            if pos.estado() == 'Abierta':
                pos.modif_precio(iol.cotizacion(token, pos.ticker()))
                pos.modif_fecha(dt.datetime.today())
        self.ordenar()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LAS FUNCIONES levantar_portfolio Y bajar_portfolio TIENEN COMO OBJETIVO MANTENER REGISTROS DE PORTFOLIOS ENTRE
# CORRIDAS DISTINTAS DEL SCRIPT. CON CADA SCRIPT EMPEZARIAMOS SIN INFO, PERO ESTAS FUNCIONES HACEN QUE MANTENGAMOS EL
# REGISTRO DEL ESTADO DE LOS PORTFOLIOS A TRAVES DEL TIEMPO Y LAS DISTINTAS EJECUCIONES
# Funcion que levanta de una ubicacion especifica el ultimo portfolio, distingue acciones del cash
def levantar_portfolio(path):
    if os.path.exists(path):
        # Busco el archivo del ultimo portfolio
        df = pd.read_csv(path, index_col='#')
        # La primera fila siempre será el cash. Se construye el objeto port de la clase Portfolio
        port = Portfolio(df.loc[0]['Valor'])
        # Se elimina del dataframe la fila del cash, quedando netamente las acciones dentro del portfolio
        df = df.drop(0).reset_index(drop=True)
        for fila in df.index:
            port.agregar_pos([p.Posicion(df.loc[fila]['Ticker'],
                                         dt.datetime.strptime(df.loc[fila]['Fecha Compra'], '%Y-%m-%d').date(),
                                         df.loc[fila]['Precio Compra'],
                                         df.loc[fila]['Cantidad'],
                                         df.loc[fila]['Estado'],
                                         dt.datetime.strptime(df.loc[fila]['Fecha Venta'], '%Y-%m-%d').date(),
                                         df.loc[fila]['Precio Venta'])])
    else:
        port = Portfolio()
    return port


# Funcion que registra un portfolio en un archivo de forma que levantándolo con la funcion correspondiente se pueda
# reconstruir igual que en la ejecucion previa del script
def bajar_portfolio(port, path):
    if 'Seguimiento' not in os.listdir('.'):
        os.mkdir('Seguimiento')
    port.registro_port().to_csv(path, index=True, index_label='#')
