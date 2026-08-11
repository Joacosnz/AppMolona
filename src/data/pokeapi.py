# Archivo: pokeapi.py
# Toda la comunicación con PokeAPI vive acá. Ningún otro módulo debería
# importar httpx directamente — si el día de mañana cambia la fuente de
# datos, este es el único archivo que se toca.

import httpx

BASE_URL = "https://pokeapi.co/api/v2"


def obtener_pokemon(nombre_o_id):
    """Trae TODOS los datos de un Pokémon puntual: stats, tipos, habilidades, sprites, etc."""
    url = f"{BASE_URL}/pokemon/{str(nombre_o_id).lower()}"
    respuesta = httpx.get(url)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_especie(nombre_o_id):
    """
    Trae datos de la 'especie' del Pokémon: descripción de Pokédex en
    varios idiomas, grupos huevo, tasa de captura, y la URL de su
    cadena evolutiva (necesaria para obtener_cadena_evolutiva).
    """
    url = f"{BASE_URL}/pokemon-species/{str(nombre_o_id).lower()}"
    respuesta = httpx.get(url)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_generacion(numero_o_nombre):
    """
    Trae los datos de UNA generación puntual (ej: 3, o "generation-iii"),
    incluyendo la lista completa de Pokémon que existen en esa generación.
    """
    respuesta = httpx.get(f"{BASE_URL}/generation/{str(numero_o_nombre).lower()}")
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_cadena_evolutiva(url_cadena):
    """
    Trae la cadena evolutiva completa. 'url_cadena' viene siempre de
    obtener_especie(...)["evolution_chain"]["url"] -- por eso acá NO
    armamos la URL nosotros mismos, la usamos tal cual viene.
    """
    respuesta = httpx.get(url_cadena)
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_encuentros(nombre_o_id):
    """Trae en qué lugares (y en qué juegos) se puede encontrar un Pokémon en estado salvaje."""
    url = f"{BASE_URL}/pokemon/{str(nombre_o_id).lower()}/encounters"
    respuesta = httpx.get(url)
    respuesta.raise_for_status()
    return respuesta.json()


def listar_tipos():
    """Trae la lista de todos los tipos existentes (fuego, agua, dragón, etc.)."""
    respuesta = httpx.get(f"{BASE_URL}/type")
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_tipo(nombre_tipo):
    """Trae todos los Pokémon que pertenecen a un tipo puntual."""
    respuesta = httpx.get(f"{BASE_URL}/type/{nombre_tipo.lower()}")
    respuesta.raise_for_status()
    return respuesta.json()


def listar_generaciones():
    """Trae la lista de TODAS las generaciones existentes (solo nombres, sin sus Pokémon)."""
    respuesta = httpx.get(f"{BASE_URL}/generation")
    respuesta.raise_for_status()
    return respuesta.json()


def obtener_stats(datos_pokemon):
    """Recibe el diccionario completo de obtener_pokemon() y devuelve solo los stats base, aplanados."""
    stats_planos = {}
    for stat_individual in datos_pokemon["stats"]:
        nombre_stat = stat_individual["stat"]["name"]
        valor_stat = stat_individual["base_stat"]
        stats_planos[nombre_stat] = valor_stat
    return stats_planos


def obtener_habilidades(datos_pokemon):
    """Devuelve solo los NOMBRES de las habilidades, como lista simple de strings."""
    return [habilidad["ability"]["name"] for habilidad in datos_pokemon["abilities"]]


def obtener_sprite(datos_pokemon):
    """Devuelve la URL de la imagen principal (artwork oficial, mejor calidad)."""
    return datos_pokemon["sprites"]["other"]["official-artwork"]["front_default"]


def sprite_url_por_id(id_pokemon):
    """
    Arma directamente la URL de la imagen oficial de un Pokémon a partir
    de su número de Pokédex, SIN hacer ningún pedido a la red -- clave
    para mostrar muchas imágenes juntas en la grilla sin traer los datos
    completos de cada uno.
    """
    return (
        "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
        f"sprites/pokemon/other/official-artwork/{id_pokemon}.png"
    )


def listar_pokemon(limite=100, offset=0):
    """Trae una lista LIVIANA de Pokémon: solo nombre y URL de cada uno, sin datos completos."""
    respuesta = httpx.get(
        f"{BASE_URL}/pokemon",
        params={"limit": limite, "offset": offset},
    )
    respuesta.raise_for_status()
    return respuesta.json()