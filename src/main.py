import flet as ft

from data.database import inicializar_db
from ui.screens import crear_equipo_screen
from ui.screens import ver_equipos_screen
from ui.screens import pokedex_screen


def main(page: ft.Page):
    page.title = "Team Builder"

    inicializar_db()

    def mostrar_inicio():
        """
        Pantalla de inicio: ahora es directamente la Pokédex completa,
        con los botones de "Crear equipo" y "Ver equipos" arriba de
        todo (los arma pokedex_screen.build).
        """
        page.controls.clear()
        page.add(pokedex_screen.build(page, mostrar_crear_equipo, mostrar_ver_equipos))
        page.update()

    def mostrar_crear_equipo():
        page.controls.clear()
        page.add(crear_equipo_screen.build(page, mostrar_inicio))
        page.update()

    def mostrar_ver_equipos():
        page.controls.clear()
        page.add(ver_equipos_screen.build(page, mostrar_inicio))
        page.update()

    mostrar_inicio()


if __name__ == "__main__":
    ft.app(target=main)