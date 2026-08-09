import flet as ft

def main(page: ft.Page):
    page.title = "Pokedex App"
    page.add(ft.Text("Pedro Puto"))

if __name__ == "__main__":
    ft.app(target=main)