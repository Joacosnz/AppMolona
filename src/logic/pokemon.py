# Archivo: pokemon.py (dentro de logic/)
# Conecta la caché local (database.py) con la API real (pokeapi.py).
# Esta es la función que el resto de tu app (las pantallas) va a llamar
# para pedir un Pokémon — nunca deberían llamar a pokeapi.py directamente.

from data import database
from data import pokeapi
from logic import comparar

# Caché en memoria (no en SQLite) de todos los Pokémon: nombre + id.
# Se llena una sola vez, la primera vez que se necesita, porque pedirle
# a PokeAPI la lista completa (más de 1000 nombres) es una sola consulta,
# pero no tiene sentido repetirla cada vez que el usuario busca algo.
# Guardamos el id además del nombre porque nos permite armar la URL del
# sprite directo (ver pokeapi.sprite_url_por_id), sin pedir los datos
# completos de cada Pokémon solo para mostrar su imagen en una grilla.
_lista_pokemon_cache = None


def _extraer_id_desde_url(url):
    """
    PokeAPI da URLs con forma 'https://pokeapi.co/api/v2/pokemon/445/'.
    Esta función saca el número del final (445 en este ejemplo).
    """
    partes = [p for p in url.split("/") if p]  # descarta los "" que deja el split en los bordes
    return partes[-1]


def _obtener_lista_de_pokemon():
    """
    Devuelve la lista completa de Pokémon como una lista de diccionarios
    {"nombre": ..., "id": ...}. La trae de la red solo la primera vez;
    las siguientes veces devuelve la que ya quedó guardada en memoria.
    """
    global _lista_pokemon_cache

    if _lista_pokemon_cache is None:
        # limite=2000 alcanza para traer TODOS los Pokémon en una sola consulta
        # (PokeAPI tiene poco más de 1000 en total).
        respuesta = pokeapi.listar_pokemon(limite=2000)
        _lista_pokemon_cache = [
            {"nombre": item["name"], "id": _extraer_id_desde_url(item["url"])}
            for item in respuesta["results"]
        ]

    return _lista_pokemon_cache


def buscar_nombre_pokemon(nombre_pedido):
    """
    Busca el nombre real de UN Pokémon a partir de lo que escribió el
    usuario, tolerando errores de tipeo (usa comparar.buscar_coincidencia).
    Se usa cuando el usuario ya sabe a cuál se refiere (ej: al agregarlo
    a un equipo).

    Devuelve el nombre real (tal como lo espera PokeAPI, ej: "garchomp"),
    o None si no encontró ninguna coincidencia razonable.
    """
    nombres = [item["nombre"] for item in _obtener_lista_de_pokemon()]
    return comparar.buscar_coincidencia(nombre_pedido, nombres)


def obtener_tipos_disponibles():
    """Devuelve la lista de nombres de todos los tipos (fire, water, dragon, etc.)."""
    datos = pokeapi.listar_tipos()
    return [item["name"] for item in datos["results"]]


def obtener_generaciones_disponibles():
    """Devuelve la lista de nombres de todas las generaciones."""
    datos = pokeapi.listar_generaciones()
    return [item["name"] for item in datos["results"]]


def filtrar_por_tipo(nombre_tipo):
    """
    Devuelve todos los Pokémon de un tipo puntual, como diccionarios
    {"nombre": ..., "id": ...} -- listos para armar la grilla, igual que
    listar_todos() o buscar_varios().
    """
    datos_tipo = pokeapi.obtener_tipo(nombre_tipo)

    return [
        {
            "nombre": entrada["pokemon"]["name"],
            "id": _extraer_id_desde_url(entrada["pokemon"]["url"]),
        }
        for entrada in datos_tipo["pokemon"]
    ]


def filtrar_por_generacion(nombre_generacion):
    """
    Devuelve todos los Pokémon de una generación puntual (ej: "generation-iii"
    para Rubí/Zafiro), como diccionarios {"nombre": ..., "id": ...}.
    """
    datos_generacion = pokeapi.obtener_generacion(nombre_generacion)

    return [
        {
            "nombre": entrada["name"],
            "id": _extraer_id_desde_url(entrada["url"]),
        }
        for entrada in datos_generacion["pokemon_species"]
    ]


def ordenar(lista_pokemon, criterio):
    """
    Reordena una lista de Pokémon YA CARGADA (no pide nada nuevo a la red).
    'criterio' puede ser: "nombre_asc", "nombre_desc", "numero_asc", "numero_desc".
    """
    if criterio == "nombre_asc":
        return sorted(lista_pokemon, key=lambda p: p["nombre"])

    if criterio == "nombre_desc":
        return sorted(lista_pokemon, key=lambda p: p["nombre"], reverse=True)

    if criterio == "numero_asc":
        return sorted(lista_pokemon, key=lambda p: int(p["id"]))

    if criterio == "numero_desc":
        return sorted(lista_pokemon, key=lambda p: int(p["id"]), reverse=True)

    # Si el criterio no es ninguno de los de arriba, devolvemos la lista tal cual.
    return lista_pokemon


def listar_todos():
    """
    Devuelve la lista COMPLETA de Pokémon (sin filtrar), como diccionarios
    {"nombre": ..., "id": ...}. Se usa para mostrar la Pokédex completa
    al entrar a la pantalla, antes de que el usuario busque nada.
    """
    return _obtener_lista_de_pokemon()


def buscar_varios(texto, max_resultados=None):
    """
    Busca TODOS los Pokémon cuyo nombre contenga el texto pedido (no solo
    el mejor match). Se usa para filtrar la grilla de la Pokédex mientras
    el usuario escribe.

    Si 'max_resultados' es None (por defecto), devuelve TODAS las
    coincidencias, sin cortar la lista.

    Devuelve una lista de diccionarios {"nombre": ..., "id": ...}.
    """
    texto = texto.strip().lower()

    todos = _obtener_lista_de_pokemon()

    if not texto:
        return todos

    coincidencias = [item for item in todos if texto in item["nombre"]]

    if max_resultados is not None:
        coincidencias = coincidencias[:max_resultados]

    return coincidencias


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