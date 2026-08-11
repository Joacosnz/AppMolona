# Archivo: pokemon.py (dentro de logic/)
# Conecta la caché local (database.py) con la API real (pokeapi.py), y
# tiene toda la lógica de búsqueda, filtrado y armado de datos "listos
# para mostrar" que usan las pantallas.

from data import database
from data import pokeapi
from logic import comparar

# Caché en memoria (no en SQLite) de todos los Pokémon: nombre + id.
# Se llena una sola vez, la primera vez que se necesita.
_lista_pokemon_cache = None

# Nombres en español de las ediciones de los juegos, para mostrar en el
# filtro de "Juego". PokeAPI solo nos da el slug en inglés (ej: "firered"),
# así que lo traducimos acá mismo -- la lista de juegos "core" es fija,
# no hace falta pedirle esto a ninguna API.
NOMBRES_JUEGOS = {
    "red": "Rojo", "blue": "Azul", "yellow": "Amarillo", "green": "Verde",
    "gold": "Oro", "silver": "Plata", "crystal": "Cristal",
    "ruby": "Rubí", "sapphire": "Zafiro", "emerald": "Esmeralda",
    "firered": "Rojo Fuego", "leafgreen": "Verde Hoja",
    "diamond": "Diamante", "pearl": "Perla", "platinum": "Platino",
    "heartgold": "Oro HeartGold", "soulsilver": "Plata SoulSilver",
    "black": "Negro", "white": "Blanco", "black-2": "Negro 2", "white-2": "Blanco 2",
    "x": "X", "y": "Y", "omega-ruby": "Rubí Omega", "alpha-sapphire": "Zafiro Alfa",
    "sun": "Sol", "moon": "Luna", "ultra-sun": "Ultrasol", "ultra-moon": "Ultraluna",
    "lets-go-pikachu": "Let's Go, Pikachu!", "lets-go-eevee": "Let's Go, Eevee!",
    "sword": "Espada", "shield": "Escudo",
    "brilliant-diamond": "Diamante Brillante", "shining-pearl": "Perla Reluciente",
    "legends-arceus": "Leyendas Arceus",
    "scarlet": "Escarlata", "violet": "Púrpura",
}


def _extraer_id_desde_url(url):
    """PokeAPI da URLs con forma 'https://pokeapi.co/api/v2/pokemon/445/'. Esto saca el 445."""
    partes = [p for p in url.split("/") if p]
    return partes[-1]


def _obtener_lista_de_pokemon():
    """Devuelve la lista completa de Pokémon {"nombre":..., "id":...}, cacheada en memoria."""
    global _lista_pokemon_cache

    if _lista_pokemon_cache is None:
        respuesta = pokeapi.listar_pokemon(limite=2000)
        _lista_pokemon_cache = [
            {"nombre": item["name"], "id": _extraer_id_desde_url(item["url"])}
            for item in respuesta["results"]
        ]

    return _lista_pokemon_cache


def buscar_nombre_pokemon(nombre_pedido):
    """Busca el nombre real de UN Pokémon, tolerando errores de tipeo. Devuelve el nombre o None."""
    nombres = [item["nombre"] for item in _obtener_lista_de_pokemon()]
    return comparar.buscar_coincidencia(nombre_pedido, nombres)


def _limpiar_texto(texto):
    """Saca saltos de línea y caracteres de control raros de las descripciones de PokeAPI."""
    return texto.replace("\n", " ").replace("\x0c", " ").replace("\f", " ")


def obtener_descripcion(nombre_o_id):
    """Devuelve la descripción de Pokédex en español si existe, o en inglés si no."""
    especie = pokeapi.obtener_especie(nombre_o_id)
    entradas = especie["flavor_text_entries"]

    for entrada in entradas:
        if entrada["language"]["name"] == "es":
            return _limpiar_texto(entrada["flavor_text"])

    for entrada in entradas:
        if entrada["language"]["name"] == "en":
            return _limpiar_texto(entrada["flavor_text"])

    return "Sin descripción disponible."


def obtener_cadena_evolutiva(nombre_o_id):
    """
    Devuelve la cadena evolutiva completa como lista ordenada de
    {"nombre":..., "id":..., "nivel":...}. 'nivel' es el nivel al que
    evoluciona A ese Pokémon (None para el primero de la cadena).
    """
    especie = pokeapi.obtener_especie(nombre_o_id)
    datos_cadena = pokeapi.obtener_cadena_evolutiva(especie["evolution_chain"]["url"])

    resultado = []

    def recorrer(nodo, nivel_para_llegar_aqui):
        resultado.append({
            "nombre": nodo["species"]["name"],
            "id": _extraer_id_desde_url(nodo["species"]["url"]),
            "nivel": nivel_para_llegar_aqui,
        })
        for siguiente in nodo["evolves_to"]:
            detalles = siguiente["evolution_details"]
            nivel = detalles[0].get("min_level") if detalles else None
            recorrer(siguiente, nivel)

    recorrer(datos_cadena["chain"], None)
    return resultado


def calcular_resistencias_y_debilidades(nombres_tipos):
    """
    Combina todos los tipos de un Pokémon y calcula contra qué tipos de
    ataque es débil, resistente o inmune. Devuelve
    {"debilidades": [...], "resistencias": [...], "inmunidades": [...]}
    con tuplas (tipo_atacante, multiplicador).
    """
    multiplicadores = {}

    for nombre_tipo in nombres_tipos:
        datos_tipo = pokeapi.obtener_tipo(nombre_tipo)
        relaciones = datos_tipo["damage_relations"]

        for entrada in relaciones["double_damage_from"]:
            t = entrada["name"]
            multiplicadores[t] = multiplicadores.get(t, 1) * 2

        for entrada in relaciones["half_damage_from"]:
            t = entrada["name"]
            multiplicadores[t] = multiplicadores.get(t, 1) * 0.5

        for entrada in relaciones["no_damage_from"]:
            t = entrada["name"]
            multiplicadores[t] = multiplicadores.get(t, 1) * 0

    debilidades = [(t, m) for t, m in multiplicadores.items() if m > 1]
    resistencias = [(t, m) for t, m in multiplicadores.items() if 0 < m < 1]
    inmunidades = [(t, m) for t, m in multiplicadores.items() if m == 0]

    return {"debilidades": debilidades, "resistencias": resistencias, "inmunidades": inmunidades}


def obtener_ubicaciones_por_juego(nombre_o_id):
    """Devuelve {"nombre_del_juego": ["lugar1", "lugar2", ...]} con dónde se encuentra este Pokémon."""
    encuentros = pokeapi.obtener_encuentros(nombre_o_id)

    resultado = {}
    for lugar in encuentros:
        nombre_lugar = lugar["location_area"]["name"]
        for detalle_version in lugar["version_details"]:
            juego = detalle_version["version"]["name"]
            resultado.setdefault(juego, [])
            if nombre_lugar not in resultado[juego]:
                resultado[juego].append(nombre_lugar)

    return resultado


def obtener_tipos_disponibles():
    """Devuelve la lista de nombres de todos los tipos existentes."""
    datos = pokeapi.listar_tipos()
    return [item["name"] for item in datos["results"]]


def obtener_generaciones_disponibles():
    """Devuelve la lista de nombres de todas las generaciones existentes."""
    datos = pokeapi.listar_generaciones()
    return [item["name"] for item in datos["results"]]


def obtener_juegos_de_generacion(nombre_generacion):
    """
    Devuelve las ediciones de juego que salieron en una generación
    puntual, ej para "generation-i": Rojo, Azul, Amarillo, Verde.

    Cada elemento es un diccionario:
      - "version_slug": identificador único de esa edición (lo que
        guarda el dropdown como value), ej "firered".
      - "grupo_slug": el "grupo de versión" al que pertenece (ej
        "firered-leafgreen"), necesario para filtrar_por_juego().
      - "nombre": nombre en español para mostrar en pantalla.
    """
    datos_generacion = pokeapi.obtener_generacion(nombre_generacion)

    juegos = []
    vistos = set()

    for grupo in datos_generacion["version_groups"]:
        grupo_slug = grupo["name"]
        datos_grupo = pokeapi.obtener_grupo_version(grupo_slug)

        for version in datos_grupo["versions"]:
            version_slug = version["name"]

            if version_slug in vistos:
                continue
            vistos.add(version_slug)

            juegos.append({
                "version_slug": version_slug,
                "grupo_slug": grupo_slug,
                "nombre": NOMBRES_JUEGOS.get(version_slug, version_slug.replace("-", " ").title()),
            })

    return juegos


def filtrar_por_tipo(nombre_tipo):
    """Devuelve todos los Pokémon de un tipo puntual, como {"nombre":..., "id":...}."""
    datos_tipo = pokeapi.obtener_tipo(nombre_tipo)
    return [
        {
            "nombre": entrada["pokemon"]["name"],
            "id": _extraer_id_desde_url(entrada["pokemon"]["url"]),
        }
        for entrada in datos_tipo["pokemon"]
    ]


def filtrar_por_generacion(nombre_generacion):
    """Devuelve todos los Pokémon de una generación puntual, como {"nombre":..., "id":...}."""
    datos_generacion = pokeapi.obtener_generacion(nombre_generacion)
    return [
        {
            "nombre": entrada["name"],
            "id": _extraer_id_desde_url(entrada["url"]),
        }
        for entrada in datos_generacion["pokemon_species"]
    ]


def filtrar_por_juego(grupo_slug):
    """
    Devuelve todos los Pokémon que pertenecen a la Pokédex regional de
    un grupo de versión puntual (ej: "diamond-pearl"), como diccionarios
    {"nombre": ..., "id": ...}.

    Usamos la Pokédex REGIONAL (la primera que trae ese grupo de
    versión) en vez de la Nacional, porque es la que de verdad refleja
    qué Pokémon aparecen en esa edición del juego.
    """
    datos_grupo = pokeapi.obtener_grupo_version(grupo_slug)

    if not datos_grupo["pokedexes"]:
        return []

    nombre_pokedex = datos_grupo["pokedexes"][0]["name"]
    datos_pokedex = pokeapi.obtener_pokedex(nombre_pokedex)

    nombres_en_el_juego = {
        entrada["pokemon_species"]["name"] for entrada in datos_pokedex["pokemon_entries"]
    }

    # La Pokédex regional no trae el "id" nacional (el que necesitamos
    # para armar la URL del sprite) -- lo sacamos de la lista completa
    # que ya tenemos en caché.
    todos = _obtener_lista_de_pokemon()

    return [item for item in todos if item["nombre"] in nombres_en_el_juego]


def ordenar(lista_pokemon, criterio):
    """Reordena una lista YA CARGADA (no pide nada nuevo a la red). No modifica QUÉ se muestra."""
    if criterio == "nombre_asc":
        return sorted(lista_pokemon, key=lambda p: p["nombre"])
    if criterio == "nombre_desc":
        return sorted(lista_pokemon, key=lambda p: p["nombre"], reverse=True)
    if criterio == "numero_asc":
        return sorted(lista_pokemon, key=lambda p: int(p["id"]))
    if criterio == "numero_desc":
        return sorted(lista_pokemon, key=lambda p: int(p["id"]), reverse=True)
    return lista_pokemon


def listar_todos():
    """Devuelve la lista COMPLETA de Pokémon, sin filtrar."""
    return _obtener_lista_de_pokemon()


def buscar_varios(texto, max_resultados=None):
    """Busca TODOS los Pokémon cuyo nombre contenga el texto pedido. Sin límite si max_resultados es None."""
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
    Devuelve los datos completos de un Pokémon, priorizando la caché
    local (SQLite) antes de pedirlo a la red.
    """
    nombre_o_id = str(nombre_o_id).lower()

    datos_en_cache = database.obtener_de_cache(nombre_o_id)
    if datos_en_cache is not None:
        return datos_en_cache

    datos_de_la_api = pokeapi.obtener_pokemon(nombre_o_id)
    database.guardar_en_cache(nombre_o_id, datos_de_la_api)
    return datos_de_la_api


def obtener_stats_de_pokemon(nombre_o_id):
    """Atajo: trae el Pokémon (con caché) y devuelve solo sus stats."""
    datos = obtener_pokemon(nombre_o_id)
    return pokeapi.obtener_stats(datos)


def obtener_habilidades_de_pokemon(nombre_o_id):
    """Atajo: trae el Pokémon (con caché) y devuelve solo sus habilidades."""
    datos = obtener_pokemon(nombre_o_id)
    return pokeapi.obtener_habilidades(datos)


def obtener_sprite_de_pokemon(nombre_o_id):
    """Atajo: trae el Pokémon (con caché) y devuelve solo la URL de su sprite."""
    datos = obtener_pokemon(nombre_o_id)
    return pokeapi.obtener_sprite(datos)