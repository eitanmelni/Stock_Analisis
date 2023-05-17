import matplotlib
import pandas as pd
import os
import datetime as dt
import matplotlib.pyplot as plt
import acciones as acc


# Funcion que se encarga de explorar que csv hay, los importa, los grafica y guarda todos los graficos
def graficos_velas(dias=180, definicion=600):
    matplotlib.interactive(False)
    # Traigo una lista con los nombres de los archivos csv con la serie historica de las acciones
    archivos = os.listdir('Stocks Data')
    graficado = []
    print('\nSTATUS GRAFICOS:')
    # EMPIEZA EL LOOP PARA RECORRER CADA UNO Y GRAFICARLO
    for archivo in archivos:
        # Traigo la data de un CSV
        df = pd.read_csv(f'Stocks Data/{archivo}', index_col='Fecha', parse_dates=True)
        # Corto el dataset en las fechas de interes, cambio los nombres de algunas columnas y agrego una columna
        # con el numero de la fila
        prices = df.loc[df.index >= dt.datetime.today() - dt.timedelta(days=dias)]
        prices = prices.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Adj Close': 'close'})
        prices['num_fila'] = range(1, len(prices) + 1)

        # DEFINICION DE COLORES
        # Defino el verde para las subas y el rojo para las bajas en las velas del precio
        col1 = 'green'
        col2 = 'red'
        # Casi negro, para los fondos de los graficos y de la ventana total
        col3 = '#1E1F22'
        # Gris claro, para las grillas, los ejes y los contornos de graficos
        col4 = '#969696'
        # Gris muy claro, para el marcado del ultimo precio de cierre
        col5 = '#E6E6E6'
        # Celeste, para el máximo absoluto y local
        col6 = '#B3FFFF'
        # Celeste mas claro, para la etiqueta de los maximos abs y local
        col7 = '#8FCCCC'
        # Violeta, para la etiqueta del minimo local y la linea que lo marca
        col8 = '#702385'
        # Violeta claro, para el relleno de la etiqueta del minimo local
        col9 = '#C3ABFF'
        # Amarillo, para el histograma del MACD
        col10 = 'yellow'
        # Verde oscuro, para el rectángulo con transparencia del RSI
        col11 = '#338A3A'

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # CREACION DE LA FIGURA
        # Creo el objeto tipo Figure que contendrá al gráfico con 4 subplots y con una proporción de tamaño definida
        fig, axs = plt.subplots(nrows=4, ncols=1, gridspec_kw={'height_ratios': [5, 1, 1, 0]})

        # Seteo el fondo de la ventana donde se van a plotear los gráficos
        fig.patch.set_facecolor(col3)

        # Asigno un nombre a los 4 objetos que van a contener los subploteos con su posición ya asignada
        ax = axs[0]
        ax2 = axs[1]
        ax3 = axs[2]
        ax4 = axs[3]

        # Ajusto márgenes de los subploteos
        plt.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95, hspace=0.05)

        # Pongo un titulo al grafico
        fig.suptitle(f'{archivo.split(".")[0]} ({acc.search_key(archivo.split(".")[0], acc.tickers).split(".")[0]})',
                     color=col4)

        # ~~~~~~~~~~~ GRAFICO DE PRECIOS ~~~~~~~~~~~
        # Defino el ancho de cada parte de las velas
        width = 0.7
        width2 = 0.08

        # Defino el color de fondo del grafico
        ax.set_facecolor(col3)

        # Agrego la grilla para los 2 ejes, definiendo su color y su linea
        ax.grid(True, which='both', color=col4, linewidth=0.2, linestyle="--")
        ax.set_axisbelow(True)
        ax.tick_params(axis='x', which='both', bottom=False, top=False)

        # TRAZADO GRAFICO VELAS
        # Defino cuando el precio sube y cuando baja segun los precios de apertura y cierre de cada dia
        up = prices[prices.close >= prices.open]
        down = prices[prices.close < prices.open]

        # Ploteo las velas en las que el precio sube
        ax.bar(up.num_fila, up.close - up.open, width, bottom=up.open, color=col1)
        ax.bar(up.num_fila, up.high - up.close, width2, bottom=up.close, color=col1)
        ax.bar(up.num_fila, up.low - up.open, width2, bottom=up.open, color=col1)
        # Ploteo las velas en las que el precio baja
        ax.bar(down.num_fila, down.close - down.open, width, bottom=down.open, color=col2)
        ax.bar(down.num_fila, down.high - down.open, width2, bottom=down.open, color=col2)
        ax.bar(down.num_fila, down.low - down.close, width2, bottom=down.close, color=col2)

        # Trazo el Ultimo precio de cierre y le coloco la etiqueta
        ax.axhline(y=prices.close[-1], color=col5, linewidth=0.5)
        ax.text(prices.num_fila[0] + 20, prices.close[-1], f'{prices.close[-1]}', size=5, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.2", fc=col5, ec=col4, lw=0.5))

        # Trazo el Maximo Absoluto y le coloco su etiqueta
        ax.plot(prices.num_fila, prices.AbsMax, color=col6, linewidth=0.5)
        ax.text(prices.num_fila[0] + 10,
                prices.AbsMax.mean(),
                f'{round(prices.AbsMax.mean(), 2)}',
                size=5,
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.2",
                          fc=col6,
                          ec=col7,
                          lw=0.5))

        # Trazo el Maximo y Minimo Locales y les coloco las etiquetas
        ax.plot(prices.num_fila, prices.LocalMax, color=col6, linewidth=0.5)
        ax.text(prices.num_fila[-1] - 35,
                prices.LocalMax.mean(),
                f'{round(prices.LocalMax.mean(), 2)}',
                size=5,
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.2",
                          fc=col6,
                          ec=col7,
                          lw=0.5))
        ax.plot(prices.num_fila, prices.LocalMin, color=col8, linewidth=0.5)
        ax.text(prices.num_fila[-1] - 35,
                prices.LocalMin.mean(),
                f'{round(prices.LocalMin.mean(), 2)}',
                size=5,
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.2",
                          fc=col9,
                          ec=col8,
                          lw=0.5))

        # Retiro las etiquetas del eje x y limito los ejes x a los valores que tengo presentes
        ax.set_xticklabels([])
        ax.set_xlim(prices.num_fila[0], prices.num_fila[-1] + 1)

        # Color de las etiquetas de los ticks de los ejes
        for tick in ax.yaxis.get_major_ticks():
            tick.label1.set_color(col5)

        # Color y ancho de los bosrdes del grafico
        for spine in ax.spines.values():
            spine.set_edgecolor(col4)
            spine.set_linewidth(0.8)

        # Color de los ticks de los ejes
        ax.tick_params(axis='x', colors=col4, labelsize=5)
        ax.tick_params(axis='y', colors=col4, labelsize=5)

        # ~~~~~~~~~~~   MACD   ~~~~~~~~~~~
        # Defino el color de fondo del grafico
        ax2.set_facecolor(col3)

        # Ploteo las dos lineas y el histograma en barras
        ax2.plot(prices.num_fila, prices.MACD, color=col1, linewidth=0.5)
        ax2.plot(prices.num_fila, prices.Signal, color=col2, linewidth=0.5)
        ax2.bar(prices.num_fila, prices.Histogram, color=col10, linewidth=0.8)

        # Linea horizontal en el 0
        ax2.axhline(y=0, color=col4, linewidth=0.5, alpha=0.5)

        # Retiro las etiquetas del eje x y limito el eje x a los valores presentes
        ax2.set_xticklabels([])
        ax2.set_xlim(prices.num_fila[0], prices.num_fila[-1] + 1)

        # Color de las etiquetas de los ticks de los ejes
        for tick in ax2.yaxis.get_major_ticks():
            tick.label1.set_color(col5)

        # Color y ancho del contonro del grafico
        for spine in ax2.spines.values():
            spine.set_edgecolor(col4)
            spine.set_linewidth(0.8)

        # Color de los ticks de los ejes
        ax2.tick_params(axis='x', colors=col4, labelsize=5)
        ax2.tick_params(axis='y', colors=col4, labelsize=5)

        # ~~~~~~~~~~~   RSI   ~~~~~~~~~~~
        # Defino el color de fondo del grafico
        ax3.set_facecolor(col3)

        # Ploteo la linea del RSI
        ax3.plot(prices.num_fila, prices.RSI, color=col1, linewidth=0.5)

        # Rectángulo con transparenca de RSI
        ax3.add_patch(plt.Rectangle((prices.num_fila[0], 30), prices.num_fila[-1] + 1, 40, color=col11, alpha=0.25))

        # Lineas horizontales que son los limites del rectangulo y las señales del RSI
        ax3.axhline(y=70, color='grey', linewidth=0.5, linestyle='--')
        ax3.axhline(y=30, color='grey', linewidth=0.5, linestyle='--')

        # Retiro las etiquetas del eje x y limito el eje x a los valores presentes
        ax3.set_xticklabels([])
        ax3.set_xlim(prices.num_fila[0], prices.num_fila[-1] + 1)

        # Color de las etiquetas de los ticks del eje y
        for tick in ax3.yaxis.get_major_ticks():
            tick.label1.set_color(col5)

        # Color y ancho del contonro del grafico
        for spine in ax3.spines.values():
            spine.set_edgecolor(col4)
            spine.set_linewidth(0.8)

        # Color de los ticks de los ejes
        ax3.tick_params(axis='x', colors=col4, labelsize=5)
        ax3.tick_params(axis='y', colors=col4, labelsize=5)

        # ~~~~~~~~~~~   EJE   ~~~~~~~~~~~
        # Defino el color de fondo del grafico
        ax4.set_facecolor(col3)

        # Ploteo cualquier linea solo para tener las fechas en el eje x. En los anteriores graficos, el eje x tiene
        # el numero
        # de fila de la tabla debido a que de esa forma no se grafican los fines de semana
        ax4.plot(prices.index, prices.num_fila, color=col4, linewidth=0.5)

        # Esta vez retiro los tick y las etiquetas de valores del eje y, y limito el eje x a los valores que estan
        # presentes
        ax4.set_yticks([])
        ax4.set_xlim(prices.index[0], prices.index[-1] + dt.timedelta(days=1))

        # Color de las etiquetas de los ticks del eje x
        for tick in ax4.xaxis.get_major_ticks():
            tick.label1.set_color(col5)

        # Color y ancho del contonro del grafico
        for spine in ax4.spines.values():
            spine.set_edgecolor(col4)
            spine.set_linewidth(0.8)

        # Color de los ticks de los ejes
        ax4.tick_params(axis='x', colors=col4, labelsize=5)
        ax4.tick_params(axis='y', colors=col4, labelsize=5)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        '''
        # Hacer display del grafico
        plt.show()
        '''

        # GUARDADO DEL GRAFICO EN UNA CARPETA CREADA PARA ESTE FIN
        if 'Stocks Grafs' not in os.listdir('.'):
            os.mkdir('Stocks Grafs')
        fig.savefig(f'Stocks Grafs/{archivo.split(".")[0]}.jpg', dpi=definicion)

        # Updateo al usuario sobre los graficos ya guardados. Lo mismo con la lista que devuelve la funcion
        print(f'- {archivo.split(".")[0]}')
        graficado.append(archivo.split(".")[0])

    return graficado


def grafico_portfolio(portfolio, archivo, definicion=800):
    matplotlib.interactive(False)
    colores = ['#3EB352', '#4BBDAD', '#4B77A6', '#5F4BBD', '#A147B3', '#B53E60', '#BF6B4B', '#A8844A', '#BFAF4B',
               '#8AB547']
    valores = [portfolio.cash()]
    etiquetas = ['Disponible']

    for pos in portfolio.posiciones():
        valores.append(pos.valor())
        etiquetas.append(pos.nombre())

    etiquetas_completas = [f'{etiqueta}\n${valor:.0f}' for etiqueta, valor in zip(etiquetas, valores)]

    colores_adapt = colores[:len(valores)]

    # Creo el objeto tipo Figure que contendrá al gráfico con 4 subplots y con una proporción de tamaño definida
    fig, ax = plt.subplots(nrows=1, ncols=1)

    # Seteo el fondo de la ventana donde se van a plotear los gráficos
    fig.patch.set_facecolor('#1E1F22')

    ax.pie(valores, labels=etiquetas_completas, colors=colores_adapt, autopct='%1.1f%%', startangle=90,
           counterclock=False, textprops={'fontsize': 9, 'color': '#E6E6E6'})
    ax.set_title(f'Tenencias\n${sum(valores)}', fontsize=13, loc='left', color='#E6E6E6')

    ax.axis('equal')

    fig.show()

    if 'Seguimiento' not in os.listdir('.'):
        os.mkdir('Seguimiento')
    fig.savefig(f'Seguimiento/{archivo}.jpg', dpi=definicion)
