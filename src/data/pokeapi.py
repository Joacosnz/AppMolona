# Archivo: pokeapi.py
# Toda la comunicación con PokeAPI vive acá. Ningún otro módulo debería
# importar httpx directamente — si el día de mañana cambia la fuente de
# datos, este es el único archivo que se toca.

import httpx

# URL base: todas las consultas empiezan igual, solo cambia lo que va después.
BASE_URL = "https://pokeapi.co/api/v2"


def obtener_pokemon(nombre_o_id):
    """
    Trae TODOS los datos de un Pokémon puntual: stats base, tipos,
    habilidades, movimientos, sprites (imágenes).

    'nombre_o_id' puede ser:
      - el nombre en inglés, tal como lo usa PokeAPI (ej: "garchomp")
      - el número de Pokédex (ej: 445)

    Devuelve un diccionario de Python con toda esa info.
    """
    # Armamos la URL completa pegando la base + el Pokémon pedido.
    # .lower() por las dudas: PokeAPI espera el nombre en minúsculas.
    url = f"{BASE_URL}/pokemon/{str(nombre_o_id).lower()}"

    respuesta = httpx.get(url)

    # raise_for_status() revisa el código de la respuesta (como el 200
    # que viste antes). Si vino un error (ej: 404 porque el nombre no
    # existe), esta línea corta la ejecución y avisa con una excepción,
    # en vez de seguir de largo con datos vacíos o rotos.
    respuesta.raise_for_status()

    # .json() convierte el texto que vino de internet en un diccionario
    # de Python, igual que hiciste en tu prueba con Garchomp.
    return respuesta.json()


def obtener_stats(datos_pokemon):
    """
    Recibe el diccionario completo que devuelve obtener_pokemon(), y
    devuelve solo los stats base, en un formato simple:
    {"hp": 108, "attack": 130, "defense": 95, ...}

    PokeAPI trae los stats como una LISTA de diccionarios, cada uno con
    la forma {"base_stat": 108, "stat": {"name": "hp", ...}}. Esta función
    los "aplana" a algo mucho más fácil de usar en el resto de tu app.
    """
    stats_planos = {}

    for stat_individual in datos_pokemon["stats"]:
        nombre_stat = stat_individual["stat"]["name"]     # ej: "hp", "attack"
        valor_stat = stat_individual["base_stat"]           # ej: 108
        stats_planos[nombre_stat] = valor_stat

    return stats_planos


def obtener_habilidades(datos_pokemon):
    """
    Recibe el diccionario completo de un Pokémon, y devuelve solo los
    NOMBRES de sus habilidades como una lista simple de strings, ej:
    ["sand-veil", "rough-skin", "sand-force"]

    PokeAPI trae "abilities" como una lista de diccionarios con más
    información (si es habilidad oculta o no, en qué posición, etc.) —
    para tu app por ahora solo te interesa el nombre.
    """
    return [habilidad["ability"]["name"] for habilidad in datos_pokemon["abilities"]]


def obtener_sprite(datos_pokemon):
    """
    Recibe el diccionario completo de un Pokémon, y devuelve la URL de
    la imagen principal (el "artwork oficial", que es la de mejor calidad
    para mostrar en una tarjeta de la grilla de búsqueda).
    """
    return datos_pokemon["sprites"]["other"]["official-artwork"]["front_default"]


def listar_pokemon(limite=100, offset=0):
    """
    Trae una lista LIVIANA de Pokémon: solo nombre y URL de cada uno,
    sin todos sus datos completos. Se usa para armar la grilla de
    búsqueda sin tener que traer todo de una sola vez (sería lentísimo).

    'limite': cuántos Pokémon traer de una vez.
    'offset': desde qué posición arrancar (para ir pidiendo de a tandas,
              tipo paginación: primero los 100 primeros, después los
              siguientes 100, etc.).
    """
    respuesta = httpx.get(
        f"{BASE_URL}/pokemon",
        params={"limit": limite, "offset": offset},
    )
    respuesta.raise_for_status()

    return respuesta.json()  # trae algo como {"results": [{"name": ..., "url": ...}, ...]}