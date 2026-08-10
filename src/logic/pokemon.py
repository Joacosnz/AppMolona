# Archivo: pokemon.py (dentro de logic/)
# Conecta la caché local (database.py) con la API real (pokeapi.py).
# Esta es la función que el resto de tu app (las pantallas) va a llamar
# para pedir un Pokémon — nunca deberían llamar a pokeapi.py directamente.

from data import database
from data import pokeapi


def obtener_pokemon(nombre_o_id):
    """
    Devuelve los datos de un Pokémon, priorizando la caché local.

    Flujo:
      1. Preguntamos a la base SQLite si ya lo tenemos guardado.
      2. Si SÍ está en caché -> lo devolvemos directo, sin usar internet.
      3. Si NO está -> lo pedimos a PokeAPI, lo guardamos en caché para
         la próxima vez, y recién ahí lo devolvemos.
    """
    nombre_o_id = str(nombre_o_id).lower()

    # Paso 1 y 2: buscamos primero en la base local.
    datos_en_cache = database.obtener_de_cache(nombre_o_id)

    if datos_en_cache is not None:
        # Ya lo teníamos guardado -> no hace falta ir a internet.
        return datos_en_cache

    # Paso 3: no estaba en caché, lo pedimos a la API real.
    datos_de_la_api = pokeapi.obtener_pokemon(nombre_o_id)

    # Lo guardamos para que la PRÓXIMA vez que alguien lo pida,
    # ya esté disponible sin necesidad de internet.
    database.guardar_en_cache(nombre_o_id, datos_de_la_api)

    return datos_de_la_api


def obtener_stats_de_pokemon(nombre_o_id):
    """
    Atajo: trae el Pokémon (usando caché si puede) y devuelve
    directamente sus stats ya "aplanados", sin que quien llama esta
    función tenga que saber nada de la estructura interna de PokeAPI.
    """
    datos = obtener_pokemon(nombre_o_id)
    return pokeapi.obtener_stats(datos)


def obtener_habilidades_de_pokemon(nombre_o_id):
    """Igual que la anterior, pero devuelve solo la lista de habilidades."""
    datos = obtener_pokemon(nombre_o_id)
    return pokeapi.obtener_habilidades(datos)


def obtener_sprite_de_pokemon(nombre_o_id):
    """Igual que las anteriores, pero devuelve solo la URL de la imagen."""
    datos = obtener_pokemon(nombre_o_id)
    return pokeapi.obtener_sprite(datos)