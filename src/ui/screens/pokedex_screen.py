# Archivo: pokedex_screen.py (dentro de ui/screens/)
# Pantalla de exploración: muestra Pokémon como tarjetas (imagen + número +
# nombre), con filtro por tipo/generación y orden por nombre/número.
# Los filtros están colapsados por defecto, atrás de un botón "Filtros".

import flet as ft

from data import pokeapi
from logic import pokemon


def build(page: ft.Page, volver_al_menu):
    """Arma y devuelve el contenido de la pantalla de la Pokédex."""

    # --- Estado de la pantalla ---
    estado = {"lista_actual": [], "filtros_visibles": False}

    # --- Controles de filtro y orden ---

    campo_busqueda = ft.TextField(label="Buscar Pokémon", width=200)

    dropdown_tipo = ft.Dropdown(
        label="Tipo",
        width=150,
        options=[ft.dropdown.Option("todos", "Todos")]
        + [ft.dropdown.Option(t) for t in pokemon.obtener_tipos_disponibles()],
        value="todos",
    )

    dropdown_generacion = ft.Dropdown(
        label="Generación",
        width=170,
        options=[ft.dropdown.Option("todas", "Todas")]
        + [ft.dropdown.Option(g) for g in pokemon.obtener_generaciones_disponibles()],
        value="todas",
    )

    dropdown_orden = ft.Dropdown(
        label="Ordenar por",
        width=180,
        options=[
            ft.dropdown.Option("nombre_asc", "Nombre (A-Z)"),
            ft.dropdown.Option("nombre_desc", "Nombre (Z-A)"),
            ft.dropdown.Option("numero_asc", "Número (menor a mayor)"),
            ft.dropdown.Option("numero_desc", "Número (mayor a menor)"),
        ],
        value="numero_asc",
    )

    texto_estado = ft.Text("", size=12, color=ft.Colors.GREY)

    grilla_resultados = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=120,
        child_aspect_ratio=0.75,
        spacing=10,
        run_spacing=10,
    )

    # --- Funciones de interacción ---

    def abrir_detalle(nombre_pokemon):
        datos = pokemon.obtener_pokemon(nombre_pokemon)
        stats = pokeapi.obtener_stats(datos)
        habilidades = pokeapi.obtener_habilidades(datos)
        sprite = pokeapi.obtener_sprite(datos)

        filas_stats = [
            ft.Text(f"{nombre_stat}: {valor}") for nombre_stat, valor in stats.items()
        ]

        dialogo = ft.AlertDialog(
            title=ft.Text(f"#{datos['id']} {nombre_pokemon.capitalize()}"),
            content=ft.Column(
                [
                    ft.Image(src=sprite, width=120, height=120),
                    ft.Text("Stats base:", weight=ft.FontWeight.BOLD),
                    *filas_stats,
                    ft.Text("Habilidades:", weight=ft.FontWeight.BOLD),
                    ft.Text(", ".join(habilidades)),
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())],
        )

        def cerrar_dialogo():
            dialogo.open = False
            page.update()

        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    def armar_tarjeta(item):
        sprite_url = pokeapi.sprite_url_por_id(item["id"])

        return ft.Container(
            content=ft.Column(
                [
                    ft.Image(src=sprite_url, width=80, height=80, fit=ft.BoxFit.CONTAIN),
                    ft.Text(f"#{item['id']}", size=10, color=ft.Colors.GREY),
                    ft.Text(item["nombre"], size=12, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            on_click=lambda e, nombre=item["nombre"]: abrir_detalle(nombre),
            border_radius=10,
            padding=6,
            ink=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
        )

    def dibujar_grilla():
        """Ordena estado['lista_actual'] según el dropdown de orden y redibuja. No pide nada a la red."""
        lista_ordenada = pokemon.ordenar(estado["lista_actual"], dropdown_orden.value)

        grilla_resultados.controls.clear()

        if len(lista_ordenada) == 0:
            texto_estado.value = "No encontré ningún Pokémon con esos filtros."
        else:
            texto_estado.value = f"{len(lista_ordenada)} Pokémon"
            for item in lista_ordenada:
                grilla_resultados.controls.append(armar_tarjeta(item))

        page.update()

    def resetear_otros_filtros(excepto):
        """Como los filtros no se combinan entre sí, usar uno resetea los demás."""
        if excepto != "busqueda":
            campo_busqueda.value = ""
        if excepto != "tipo":
            dropdown_tipo.value = "todos"
        if excepto != "generacion":
            dropdown_generacion.value = "todas"

    def buscar(e):
        resetear_otros_filtros(excepto="busqueda")
        estado["lista_actual"] = pokemon.buscar_varios(campo_busqueda.value)
        dibujar_grilla()

    def cambio_tipo(e):
        resetear_otros_filtros(excepto="tipo")
        if dropdown_tipo.value == "todos":
            estado["lista_actual"] = pokemon.listar_todos()
        else:
            estado["lista_actual"] = pokemon.filtrar_por_tipo(dropdown_tipo.value)
        dibujar_grilla()

    def cambio_generacion(e):
        resetear_otros_filtros(excepto="generacion")
        if dropdown_generacion.value == "todas":
            estado["lista_actual"] = pokemon.listar_todos()
        else:
            estado["lista_actual"] = pokemon.filtrar_por_generacion(dropdown_generacion.value)
        dibujar_grilla()

    def cambio_orden(e):
        dibujar_grilla()

    def restablecer_filtros(e):
        """Vuelve todo a su estado original: sin búsqueda, sin filtro, orden por número."""
        campo_busqueda.value = ""
        dropdown_tipo.value = "todos"
        dropdown_generacion.value = "todas"
        dropdown_orden.value = "numero_asc"
        estado["lista_actual"] = pokemon.listar_todos()
        dibujar_grilla()  # ya hace su propio page.update()

    def alternar_filtros(e):
        """Muestra u oculta el panel de filtros al tocar el botón 'Filtros'."""
        estado["filtros_visibles"] = not estado["filtros_visibles"]
        panel_filtros.visible = estado["filtros_visibles"]
        boton_filtros.text = "Ocultar filtros" if estado["filtros_visibles"] else "Filtros"
        page.update()

    dropdown_tipo.on_change = cambio_tipo
    dropdown_generacion.on_change = cambio_generacion
    dropdown_orden.on_change = cambio_orden

    boton_buscar = ft.ElevatedButton("Buscar", on_click=buscar)
    boton_volver = ft.ElevatedButton("Volver al menú", on_click=lambda e: volver_al_menu())
    boton_filtros = ft.OutlinedButton("Filtros", icon=ft.Icons.FILTER_LIST, on_click=alternar_filtros)
    boton_restablecer = ft.TextButton(
        "Restablecer filtros", icon=ft.Icons.REFRESH, on_click=restablecer_filtros
    )

    # Panel de filtros: arranca oculto (visible=False), se despliega al
    # tocar el botón "Filtros".
    panel_filtros = ft.Container(
        content=ft.Column(
            [
                ft.Row([dropdown_tipo, dropdown_generacion, dropdown_orden], wrap=True),
                boton_restablecer,
            ]
        ),
        visible=estado["filtros_visibles"],
        padding=ft.Padding.only(top=10),
    )

    # Al entrar a la pantalla, mostramos TODOS los Pokémon.
    estado["lista_actual"] = pokemon.listar_todos()
    dibujar_grilla()

    return ft.Column(
        [
            ft.Text("Pokédex", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([campo_busqueda, boton_buscar, boton_filtros]),
            panel_filtros,
            texto_estado,
            grilla_resultados,
            boton_volver,
        ],
        expand=True,
    )