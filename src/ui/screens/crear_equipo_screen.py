# Archivo: crear_equipo_screen.py (dentro de ui/screens/)
# Pantalla para armar un equipo nuevo: buscar Pokémon, elegir habilidad,
# agregarlos a la lista, y guardar el equipo completo en la base local.

import flet as ft

from logic import pokemon
from data import pokeapi, database


def build(page: ft.Page, volver_al_menu):
    """
    Arma y devuelve el contenido de la pantalla de "Crear equipo".

    'page' es la página de Flet (la necesitamos para poder refrescar la
    interfaz con page.update() cada vez que algo cambia).

    'volver_al_menu' es una función que nos pasan desde afuera (main.py)
    para poder volver a la pantalla anterior cuando el usuario termine
    -- así esta pantalla no necesita saber nada de cómo está armada la
    navegación del resto de la app.
    """

    # --- Estado de la pantalla ---
    # Estas listas/variables viven mientras el usuario arma el equipo.
    # Se pierden si sale de la pantalla sin guardar (a propósito, todavía
    # no hay "guardado automático").
    pokemon_agregados = []  # cada elemento: {"nombre": ..., "habilidad": ..., "sprite": ...}

    # Guardamos acá el Pokémon que el usuario acaba de buscar, mientras
    # elige la habilidad, antes de confirmarlo y agregarlo a la lista.
    pokemon_en_progreso = {"nombre": None, "habilidades_disponibles": []}

    # --- Controles de la interfaz ---
    # Los definimos como variables porque vamos a necesitar leerlos y
    # modificarlos desde las funciones de más abajo (los "on_click").

    campo_nombre_equipo = ft.TextField(label="Nombre del equipo", width=280)
    campo_juego = ft.TextField(label="Juego (ej: Rubí y Zafiro)", width=280)

    campo_busqueda_pokemon = ft.TextField(label="Buscar Pokémon", width=200)
    texto_error_busqueda = ft.Text("", color=ft.Colors.RED, size=12)

    dropdown_habilidad = ft.Dropdown(label="Habilidad", width=200, visible=False)
    boton_confirmar_pokemon = ft.ElevatedButton(
        "Agregar al equipo", visible=False
    )

    # ft.Column es un contenedor que apila sus hijos verticalmente.
    # Acá vamos a ir agregando una fila por cada Pokémon ya confirmado.
    lista_visual_equipo = ft.Column()

    texto_contador = ft.Text("0/6 Pokémon agregados", size=12, color=ft.Colors.GREY)

    # --- Funciones que reaccionan a las acciones del usuario ---

    def buscar_pokemon(e):
        """Se ejecuta cuando el usuario aprieta 'Buscar'."""
        texto_error_busqueda.value = ""

        if len(pokemon_agregados) >= 6:
            texto_error_busqueda.value = "El equipo ya tiene 6 Pokémon."
            page.update()
            return

        nombre_pedido = campo_busqueda_pokemon.value

        # Usamos la búsqueda tolerante a errores de tipeo que armamos en logic/pokemon.py
        nombre_confirmado = pokemon.buscar_nombre_pokemon(nombre_pedido)

        if not nombre_confirmado:
            texto_error_busqueda.value = f"No encontré ningún Pokémon parecido a '{nombre_pedido}'."
            dropdown_habilidad.visible = False
            boton_confirmar_pokemon.visible = False
            page.update()
            return

        # Traemos los datos completos (usa caché SQLite si ya lo habíamos pedido antes)
        datos = pokemon.obtener_pokemon(nombre_confirmado)
        habilidades = pokeapi.obtener_habilidades(datos)
        sprite = pokeapi.obtener_sprite(datos)

        # Guardamos este Pokémon como "en progreso" mientras el usuario elige la habilidad
        pokemon_en_progreso["nombre"] = nombre_confirmado
        pokemon_en_progreso["sprite"] = sprite

        # Llenamos el dropdown con las habilidades reales de este Pokémon puntual
        dropdown_habilidad.options = [ft.dropdown.Option(h) for h in habilidades]
        dropdown_habilidad.value = habilidades[0] if habilidades else None
        dropdown_habilidad.visible = True
        boton_confirmar_pokemon.visible = True

        page.update()

    def confirmar_pokemon(e):
        """Se ejecuta cuando el usuario ya eligió la habilidad y aprieta 'Agregar al equipo'."""
        pokemon_agregados.append({
            "nombre": pokemon_en_progreso["nombre"],
            "habilidad": dropdown_habilidad.value,
            "sprite": pokemon_en_progreso["sprite"],
        })

        # Agregamos una fila visual nueva a la lista del equipo, con el
        # nombre y la habilidad elegida, para que el usuario vea qué lleva armado.
        lista_visual_equipo.controls.append(
            ft.Row([
                ft.Image(src=pokemon_en_progreso["sprite"], width=40, height=40),
                ft.Text(f"{pokemon_en_progreso['nombre']} — {dropdown_habilidad.value}"),
            ])
        )

        texto_contador.value = f"{len(pokemon_agregados)}/6 Pokémon agregados"

        # Limpiamos los campos para la próxima búsqueda
        campo_busqueda_pokemon.value = ""
        dropdown_habilidad.visible = False
        boton_confirmar_pokemon.visible = False
        pokemon_en_progreso["nombre"] = None

        page.update()

    def guardar_equipo(e):
        """Se ejecuta cuando el usuario aprieta 'Guardar equipo', al final de todo."""
        if not campo_nombre_equipo.value:
            texto_error_busqueda.value = "Ponele un nombre al equipo antes de guardar."
            page.update()
            return

        if len(pokemon_agregados) == 0:
            texto_error_busqueda.value = "Agregá al menos un Pokémon antes de guardar."
            page.update()
            return

        # 1. Creamos el equipo (vacío) en la base, y nos quedamos con su id
        id_equipo = database.crear_equipo(campo_nombre_equipo.value, campo_juego.value)

        # 2. Le agregamos cada Pokémon que el usuario armó.
        #    Los EVs arrancan todos en 0 -- se editan después, en la
        #    pantalla de edición (igual que en tu CLI original).
        evs_iniciales = {"PS": 0, "Atq": 0, "Def": 0, "Atq_Esp": 0, "Def_Esp": 0, "Vel": 0}

        for p in pokemon_agregados:
            database.agregar_pokemon_a_equipo(id_equipo, p["nombre"], p["habilidad"], evs_iniciales)

        # 3. Volvemos al menú principal
        volver_al_menu()

    # Conectamos cada botón con su función
    boton_buscar = ft.ElevatedButton("Buscar", on_click=buscar_pokemon)
    boton_confirmar_pokemon.on_click = confirmar_pokemon
    boton_guardar = ft.ElevatedButton("Guardar equipo", on_click=guardar_equipo)

    # --- Armamos y devolvemos la pantalla completa ---
    return ft.Column([
        ft.Text("Crear equipo", size=24, weight=ft.FontWeight.BOLD),
        campo_nombre_equipo,
        campo_juego,
        ft.Divider(),
        ft.Row([campo_busqueda_pokemon, boton_buscar]),
        texto_error_busqueda,
        dropdown_habilidad,
        boton_confirmar_pokemon,
        ft.Divider(),
        texto_contador,
        lista_visual_equipo,
        ft.Divider(),
        boton_guardar,
    ])