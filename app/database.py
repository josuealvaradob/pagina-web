_MARCAS = [
    "lattafa_sublime",
    "blue_chanel",
    "summer_hammer",
    "lacoste_white",
    "one_million",
    "aventus_creed",
    "invictus",
    "legend_montblanc",
    "212_vip",
]
_TAMANOS = ["30ml", "50ml", "100ml"]

INVENTARIO = {f"{marca}_{tamano}": 30 for marca in _MARCAS for tamano in _TAMANOS}
PEDIDOS = {}
CONTADOR_PEDIDOS = 0
