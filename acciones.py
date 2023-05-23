# Funcion para buscar keys de un diccionario pasando el valor
def search_key(val, dicc):
    for key, value in dicc.items():
        if val == value:
            return key
    return 'ticker'


tickers = {
    'GGAL': 'Galicia'
    , 'TXAR': 'Ternium'
    , 'CVH': 'Cablevision'
    , 'COME': 'Soc Com del Plata'
    , 'YPFD': 'YPF'
    , 'TGSU2': 'Gas del Sur'
    , 'VALO': 'Valores'
    , 'PAMP': 'Pampa'
    , 'SUPV': 'Supervielle'
    , 'ALUA': 'Aluar'
    , 'CEPU': 'Central Puertos'
    , 'TGNO4': 'Gas del Norte'
    , 'BMA': 'Macro'
    , 'MIRG': 'Mirgor'
    , 'TECO2': 'Telecom'
    , 'BBAR': 'Banco Frances'
    , 'MELI': 'Mercado Libre CEDEAR'
    , 'AMZN': 'Amazon CEDEAR'
    , 'C': 'Citigroup CEDEAR'
    , 'PYPL': 'Paypal CEDEAR'
    , 'GOOGL': 'Google CEDEAR'
    , 'TEN': 'Tenaris CEDEAR'
    , 'BYMA': 'Bolsas y Mercados Arg'
    , 'LOMA': 'Loma Negra'
    , 'TRAN': 'Transener'
    , 'HARG': 'Holcim'
    , 'BABA': 'Alibaba CEDEAR'
}

stocks = list(tickers.keys())
