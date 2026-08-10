# Archivo: ver_equipos_screen.py (dentro de ui/screens/)
# Pantalla para ver todos los equipos guardados, con sus Pokémon.

import flet as ft

from data import database
from logic import pokemon


def build(page: ft.Page, volver_al_menu):
    """
    Arma y devuelve el contenido de la pantalla "Ver equipos".

    Trae los equipos desde la base local (database.obtener_equipos), y
    para cada uno trae también sus Pokémon (database.obtener_pokemon_de_equipo).
    """

    equipos = database.obtener_equipos()

    # Columna donde vamos a apilar una "tarjeta" por cada equipo.
    # scroll=AUTO permite que se pueda desplazar si hay muchos equipos
    # y no entran todos en la pantalla.
    columna_equipos = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    if len(equipos) == 0:
        columna_equipos.controls.append(
            ft.Text("Todavía no creaste ningún equipo.", color=ft.Colors.GREY)
        )

    for equipo in equipos:
        # Traemos los Pokémon de ESTE equipo puntual, usando su id
        # (así funciona la relación equipo_id -> id que armamos con FOREIGN KEY).
        pokemones_del_equipo = database.obtener_pokemon_de_equipo(equipo["id"])

        filas_pokemon = []
        for p in pokemones_del_equipo:
            # Traemos el sprite para mostrarlo. Como este Pokémon ya se
            # consultó antes (al crearlo en crear_equipo_screen), esto
            # debería salir de la caché local, sin usar internet de nuevo.
            try:
                sprite = pokemon.obtener_sprite_de_pokemon(p["pokemon_nombre"])
            except Exception:
                # Por si algo falla (ej: sin internet y no estaba en caché),
                # mostramos un ícono genérico en vez de romper toda la pantalla.
                sprite = None

            imagen_o_icono = (
                ft.Image(src=sprite, width=32, height=32)
                if sprite
                else ft.Icon(ft.Icons.CATCHING_POKEMON, size=32)
            )

            filas_pokemon.append(
                ft.Row([
                    imagen_o_icono,
                    ft.Text(f"{p['pokemon_nombre']} — {p['habilidad']}"),
                ])
            )

        # Una "tarjeta" por equipo: nombre + juego arriba, y la lista de
        # sus Pokémon debajo.
        tarjeta_equipo = ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{equipo['nombre']} ({equipo['juego']})",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                *filas_pokemon,
            ]),
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            margin=ft.Margin.only(bottom=10),
        )

        columna_equipos.controls.append(tarjeta_equipo)

    boton_volver = ft.ElevatedButton("Volver al menú", on_click=lambda e: volver_al_menu())

    return ft.Column([
        ft.Text("Equipos guardados", size=24, weight=ft.FontWeight.BOLD),
        columna_equipos,
        boton_volver,
    ])