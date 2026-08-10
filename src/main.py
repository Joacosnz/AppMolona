import flet as ft

from data.database import inicializar_db
from ui.screens import crear_equipo_screen
from ui.screens import ver_equipos_screen
from ui.screens import pokedex_screen


def main(page: ft.Page):
    page.title = "Team Builder"

    inicializar_db()

    def mostrar_menu():
        """Limpia la pantalla y muestra el menú principal."""
        page.controls.clear()
        page.add(
            ft.Text("Team Builder", size=28, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton("Crear equipo", on_click=lambda e: mostrar_crear_equipo()),
            ft.ElevatedButton("Ver equipos", on_click=lambda e: mostrar_ver_equipos()),
            ft.ElevatedButton("Pokédex", on_click=lambda e: mostrar_pokedex()),
        )
        page.update()

    def mostrar_crear_equipo():
        page.controls.clear()
        page.add(crear_equipo_screen.build(page, mostrar_menu))
        page.update()

    def mostrar_ver_equipos():
        page.controls.clear()
        page.add(ver_equipos_screen.build(page, mostrar_menu))
        page.update()

    def mostrar_pokedex():
        page.controls.clear()
        page.add(pokedex_screen.build(page, mostrar_menu))
        page.update()

    mostrar_menu()


if __name__ == "__main__":
    ft.app(target=main)