from data import database
from logic import pokemon

database.inicializar_db()   # <- esto falta, crea las tablas si no existen

datos = pokemon.obtener_pokemon("garchomp")
print(datos)
