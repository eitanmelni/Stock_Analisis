from pandas import DataFrame, read_csv, to_datetime
from os import listdir, mkdir, path
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import interactive
import logging
import iol

# Este modulo lleva el registro de la evolucion de la cartera como un todo (cash + titulos valorizados) a lo largo del
# tiempo. IOL no guarda esa historia, asi que cada corrida del script agrega una foto del estado de cuenta a un csv.
ARCHIVO_EVOLUCION = 'Seguimiento/evolucion_cartera.csv'
COLUMNAS = ['Fecha', 'Disponible', 'Invertido', 'Total']


# Levanta el csv con la historia de la cartera. Si no existe todavia, devuelve un dataframe vacio
def levantar_evolucion(path_f=ARCHIVO_EVOLUCION):
    if path.exists(path_f):
        return read_csv(path_f, parse_dates=['Fecha'])
    return DataFrame(columns=COLUMNAS)


# Trae el estado de cuenta actual y agrega una fila al csv. Si ya hay una foto del mismo dia se pisa con la mas reciente,
# de forma que haya como maximo un punto por dia aunque se corra el script varias veces
def registrar_evolucion(path_f=ARCHIVO_EVOLUCION):
    logging.info('Se registra la foto diaria de la cartera')
    token = iol.gestor_token()
    disponible, invertido, total, _ = iol.estado_cuenta(token)

    df = levantar_evolucion(path_f)
    hoy = to_datetime(datetime.today().date())
    df = df[to_datetime(df['Fecha']) != hoy]
    df.loc[len(df)] = [hoy, disponible, invertido, total]
    df = df.sort_values('Fecha').reset_index(drop=True)

    if 'Seguimiento' not in listdir('.'):
        mkdir('Seguimiento')
    df.to_csv(path_f, index=False, date_format='%Y-%m-%d')
    return df


def grafico_evolucion(df, archivo='Evolucion', definicion=300):
    logging.info('Comienza la creación del gráfico de evolución de la cartera')
    interactive(False)
    # Casi negro para los fondos, gris claro para ejes y grillas, celeste para el total, verde y violeta para las partes
    col_fondo = '#1E1F22'
    col_ejes = '#969696'
    col_total = '#B3FFFF'
    col_invertido = '#338A3A'
    col_disponible = '#702385'

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(col_fondo)
    ax.set_facecolor(col_fondo)

    # Areas apiladas de lo invertido y lo disponible, y arriba la linea del total
    ax.stackplot(df['Fecha'], df['Invertido'], df['Disponible'], colors=[col_invertido, col_disponible], alpha=0.5,
                 labels=['Títulos valorizados', 'Disponible'])
    ax.plot(df['Fecha'], df['Total'], color=col_total, linewidth=1.5, label='Total', marker='o' if len(df) < 40 else None,
            markersize=3)

    # Etiqueta con el ultimo valor y el cambio desde el primer registro
    ultimo = df['Total'].iloc[-1]
    primero = df['Total'].iloc[0]
    cambio = f' (variación del total {ultimo / primero - 1:+.1%}, incluye aportes/retiros, desde {df["Fecha"].iloc[0]:%d/%m/%Y})' if primero and len(df) > 1 else ''
    ax.set_title(f'Evolución de la cartera: ${ultimo:,.0f}{cambio}', color=col_ejes)

    ax.grid(True, color=col_ejes, linewidth=0.2, linestyle='--')
    ax.set_axisbelow(True)
    ax.tick_params(colors=col_ejes)
    for borde in ax.spines.values():
        borde.set_color(col_ejes)
    ax.legend(loc='lower left', facecolor=col_fondo, edgecolor=col_ejes, labelcolor=col_ejes)
    fig.autofmt_xdate()

    if 'Seguimiento' not in listdir('.'):
        mkdir('Seguimiento')
    fig.savefig(f'Seguimiento/{archivo}.jpg', dpi=definicion, facecolor=fig.get_facecolor())
    plt.close(fig)
