# Funcion para buscar keys de un diccionario pasando el valor
def search_key(val, dicc):
    for key, value in dicc.items():
        if val == value:
            return key
    return 'ticker'


tickers = {
    'GGAL.BA': 'Galicia'
    , 'TXAR.BA': 'Ternium'
    , 'CVH.BA': 'Cablevision'
    , 'COME.BA': 'Soc Com del Plata'
    , 'YPFD.BA': 'YPF'
    , 'TGSU2.BA': 'Gas del Sur'
    , 'VALO.BA': 'Valores'
    , 'PAMP.BA': 'Pampa'
    , 'SUPV.BA': 'Supervielle'
    , 'ALUA.BA': 'Aluar'
    , 'CEPU.BA': 'Central Puertos'
    , 'TGNO4.BA': 'Gas del Norte'
    , 'BMA.BA': 'Macro'
    , 'MIRG.BA': 'Mirgor'
    , 'TECO2.BA': 'Telecom'
    , 'BBAR.BA': 'Banco Frances'
    , 'MELI.BA': 'Mercado Libre CEDEAR'
    , 'AMZN.BA': 'Amazon CEDEAR'
    , 'C.BA': 'Citigroup CEDEAR'
    , 'PYPL.BA': 'Paypal CEDEAR'
    , 'GOOGL.BA': 'Google CEDEAR'
    , 'TEN.BA': 'Tenaris CEDEAR'
    , 'BYMA.BA': 'Bolsas y Mercados Arg'
    , 'LOMA.BA': 'Loma Negra'
    , 'TRAN.BA': 'Transener'
    , 'HARG.BA': 'Holcim'
    , 'BABA.BA': 'Alibaba CEDEAR'
}

stocks = list(tickers.keys())
