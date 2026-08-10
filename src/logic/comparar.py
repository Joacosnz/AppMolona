# Archivo: comparar.py
# Búsqueda tolerante a errores de tipeo, genérica: sirve para nombres de
# Pokémon, movimientos, habilidades o juegos — cualquier lista de strings.

import difflib as dif


def buscar_coincidencia(texto_pedido, opciones, cutoff=0.5):
    """
    Busca 'texto_pedido' dentro de 'opciones' (lista de strings).

    Primero intenta encontrar opciones que EMPIECEN con el texto pedido
    (rápido y preciso para nombres largos, ej: "floette" -> "Floette (Flor Eterna)").
    Si no hay ninguna coincidencia así, usa difflib como respaldo para
    tolerar errores de tipeo.

    Devuelve el nombre real de la opción encontrada, o None si no hay match.
    """
    if not texto_pedido or not opciones:
        return None

    texto_pedido = texto_pedido.strip().lower()

    coincidencias = [op for op in opciones if op.lower().startswith(texto_pedido)]

    if len(coincidencias) == 1:
        return coincidencias[0]

    if len(coincidencias) > 1:
        # Si hay varias (ej: distintas formas del mismo Pokémon),
        # nos quedamos con la más corta -> normalmente la forma base.
        return min(coincidencias, key=len)

    resultado = dif.get_close_matches(texto_pedido, opciones, n=1, cutoff=cutoff)
    return resultado[0] if resultado else None