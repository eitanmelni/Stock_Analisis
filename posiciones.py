import acciones as acc
import pandas as pd
import datetime as dt


class Posicion:
    def __init__(self, ticker, fecha_c, precio_c, cantidad_titulos, estado='Abierta', fecha_v=None, precio_v=None):
        self._ticker = ticker
        self._fecha_c = fecha_c
        self._precio_c = precio_c
        self._cantidad_titulos = cantidad_titulos
        self._estado = estado
        if fecha_v is None:
            self._fecha_v = fecha_c
        else:
            self._fecha_v = fecha_v
        if precio_v is None:
            self._precio_v = precio_c
        else:
            self._precio_v = precio_v
        self._nombre = acc.tickers[f'{ticker}']
        self._inversion = self._precio_c * self._cantidad_titulos
        self._valor_actual = self._precio_v * self._cantidad_titulos
        self._resultado = self._valor_actual - self._inversion
        self._rendimiento = self._resultado / self._inversion

    def ticker(self):
        return self._ticker

    def nombre(self):
        return self._nombre

    def fecha_compra(self):
        return self._fecha_c

    def precio_compra(self):
        return self._precio_c

    def cantidad(self):
        return self._cantidad_titulos

    def estado(self):
        return self._estado

    def fecha_venta(self):
        return self._fecha_v

    def precio_venta(self):
        return self._precio_v

    def invertido(self):
        return self._inversion

    def valor(self):
        return self._valor_actual

    def resultado(self):
        return self._resultado

    def rendimiento(self):
        return self._rendimiento

    def __str__(self):
        return f'{self._nombre} ({self._ticker}):    ${self._cantidad_titulos * self._precio_v} ({round(self._cantidad_titulos)} papeles por ${self._precio_v}) || Rendimiento {round(self._rendimiento * 100, 1)}% ({self._estado})'

    def __repr__(self):
        return f'{self._ticker}: {self._cantidad_titulos} papeles por ${self._precio_v} en {self._fecha_v}, comprados a ${self._precio_v} en {self._fecha_v.date()}. La posicion esta {self._estado}'

    def __lt__(self, other):
        if self._estado != other.estado():
            return self._estado > other.estado()
        elif self._fecha_v != other.fecha_venta():
            return self._fecha_v < other.fecha_venta()
        else:
            return self._fecha_c < other.fecha_compra()

    '''def __eq__(self, other):
        return self._valor_actual == other.valor()

    def __le__(self, other):
        return self._valor_actual <= other.valor()

    def __ne__(self, other):
        return self._valor_actual != other.valor()

    def __gt__(self, other):
        return self._valor_actual > other.valor()

    def __ge__(self, other):
        return self._valor_actual >= other.valor()

    def __add__(self, other):
        return self._valor_actual + other.valor()

    def __sub__(self, other):
        return self._valor_actual - other.valor()'''

    def __len__(self):
        res = round((self._fecha_v - self._fecha_c) / dt.timedelta(days=1))
        if res > 0:
            return res
        else:
            return 1

    def __recalcular(self):
        self._inversion = self._precio_c * self._cantidad_titulos
        self._valor_actual = self._precio_v * self._cantidad_titulos
        self._resultado = self._valor_actual - self._inversion
        self._rendimiento = self._resultado / self._inversion

    def modif_estado(self, nuevo_estado):
        self._estado = nuevo_estado

    def modif_cantidad(self, nueva_cantidad):
        self._cantidad_titulos = nueva_cantidad
        self.__recalcular()

    def modif_precio(self, nuevo_precio):
        self._precio_v = nuevo_precio
        self.__recalcular()

    def modif_fecha(self, nueva_fecha):
        self._fecha_v = nueva_fecha.date()

    def registro(self):
        return [self.ticker(),
                self.fecha_compra(),
                self.precio_compra(),
                self.cantidad(),
                self.estado(),
                self.fecha_venta(),
                self.precio_venta(),
                self.valor(),
                round(self.rendimiento(), 4),
                round((self.rendimiento() + 1) ** (30 / len(self)) - 1, 4)]

    def actualizar(self):
        df = pd.read_csv(f'Stocks Data/{self._nombre}.csv', index_col='Fecha', parse_dates=True)
        self._fecha_v = df.index[-1]
        self._precio_v = df['Adj Close'][-1]
        self.__recalcular()

    def toma_ganancia(self, cant, fecha, precio):
        if cant >= self._cantidad_titulos:
            pass
        else:
            self._cantidad_titulos -= cant
            self._fecha_v = fecha
            self._precio_v = precio
            self.__recalcular()
            print(self)
            pos_cerr = Posicion(ticker=self._ticker,
                                fecha_c=self._fecha_c,
                                precio_c=self._precio_c,
                                cantidad_titulos=cant,
                                estado='Cerrada',
                                fecha_v=fecha,
                                precio_v=precio)
            print(pos_cerr)
            return pos_cerr

    def recalcular(self):
        self.__recalcular()
