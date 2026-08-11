# Archivo: pokedex_screen.py (dentro de ui/screens/)
# Esta pantalla cumple DOS roles distintos, según cómo se la llame:
#
# 1. MODO NORMAL (pantalla de inicio de la app): grilla completa +
#    ficha detallada de 2 pestañas al tocar un Pokémon. Se le pasan
#    'on_crear_equipo' y 'on_ver_equipos' para los botones de arriba.
#
# 2. MODO SELECCIÓN (modo_seleccion=True): la usa crear_equipo_screen.py
#    para elegir el Pokémon de un slot. Acá tocar una tarjeta NO abre la
#    ficha completa -- abre un diálogo chico para elegir la habilidad y
#    confirmar, y llama a 'on_pokemon_elegido(nombre, habilidad, sprite)'.
#    'on_cancelar_seleccion' se usa para volver sin elegir nada.

import flet as ft

from data import pokeapi
from logic import pokemon

COLOR_POR_TIPO = {
    "normal": "#A8A878", "fire": "#F08030", "water": "#6890F0",
    "electric": "#F8D030", "grass": "#78C850", "ice": "#98D8D8",
    "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820",
    "rock": "#B8A038", "ghost": "#705898", "dragon": "#7038F8",
    "dark": "#705848", "steel": "#B8B8D0", "fairy": "#EE99AC",
}


def _badge_tipo(nombre_tipo, sufijo=""):
    color = COLOR_POR_TIPO.get(nombre_tipo, "#777777")
    return ft.Container(
        content=ft.Text(f"{nombre_tipo}{sufijo}", size=12, color=ft.Colors.WHITE),
        bgcolor=color,
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
    )


def build(
    page: ft.Page,
    on_crear_equipo=None,
    on_ver_equipos=None,
    modo_seleccion=False,
    on_pokemon_elegido=None,
    on_cancelar_seleccion=None,
):
    """
    Arma y devuelve el contenido de la pantalla de la Pokédex.

    Parámetros de MODO NORMAL (pantalla de inicio):
        on_crear_equipo, on_ver_equipos -- funciones para los botones de arriba.

    Parámetros de MODO SELECCIÓN (usado por crear_equipo_screen.py):
        modo_seleccion=True, on_pokemon_elegido(nombre, habilidad, sprite),
        on_cancelar_seleccion -- para volver sin elegir nada.
    """

    estado = {"lista_actual": [], "filtros_visibles": False}

    # --- Controles de filtro y orden (se usan en los dos modos) ---

    campo_busqueda = ft.TextField(label="Buscar Pokémon", width=200)

    dropdown_tipo = ft.Dropdown(
        label="Tipo", width=150,
        options=[ft.dropdown.Option("todos", "Todos")]
        + [ft.dropdown.Option(t) for t in pokemon.obtener_tipos_disponibles()],
        value="todos",
    )

    dropdown_generacion = ft.Dropdown(
        label="Generación", width=170,
        options=[ft.dropdown.Option("todas", "Todas")]
        + [ft.dropdown.Option(g) for g in pokemon.obtener_generaciones_disponibles()],
        value="todas",
    )

    dropdown_orden = ft.Dropdown(
        label="Ordenar por", width=180,
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
        expand=True, runs_count=3, max_extent=120,
        child_aspect_ratio=0.75, spacing=10, run_spacing=10,
    )

    # --- MODO SELECCIÓN: diálogo chico para elegir habilidad y confirmar ---

    def abrir_seleccion(nombre_pokemon):
        datos = pokemon.obtener_pokemon(nombre_pokemon)
        habilidades = pokeapi.obtener_habilidades(datos)
        sprite = pokeapi.obtener_sprite(datos)

        dropdown_habilidad = ft.Dropdown(
            label="Habilidad",
            options=[ft.dropdown.Option(h) for h in habilidades],
            value=habilidades[0] if habilidades else None,
        )

        def confirmar(e):
            cerrar_dialogo()
            on_pokemon_elegido(nombre_pokemon, dropdown_habilidad.value, sprite)

        def cerrar_dialogo():
            dialogo.open = False
            page.update()

        dialogo = ft.AlertDialog(
            title=ft.Text(nombre_pokemon.capitalize()),
            content=ft.Column(
                [
                    ft.Image(src=sprite, width=100, height=100),
                    dropdown_habilidad,
                ],
                tight=True,
            ),
            actions=[
                ft.ElevatedButton("Agregar al equipo", on_click=confirmar),
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo()),
            ],
        )

        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    # --- MODO NORMAL: ficha completa de 2 pestañas ---

    def construir_grafico_stats(stats):
        barras = []
        valor_maximo = max(stats.values()) if stats else 1

        for nombre_stat, valor in stats.items():
            alto_barra = int((valor / valor_maximo) * 120) + 10

            barras.append(
                ft.Column(
                    [
                        ft.Text(str(valor), size=11),
                        ft.Container(
                            width=24, height=alto_barra,
                            bgcolor=ft.Colors.GREEN_400,
                            border_radius=4,
                        ),
                        ft.Text(nombre_stat, size=10, color=ft.Colors.GREY),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                )
            )

        return ft.Row(barras, alignment=ft.MainAxisAlignment.SPACE_EVENLY)

    def abrir_detalle(nombre_pokemon):
        datos = pokemon.obtener_pokemon(nombre_pokemon)
        stats = pokeapi.obtener_stats(datos)
        habilidades = pokeapi.obtener_habilidades(datos)
        sprite_normal = datos["sprites"]["front_default"]
        sprite_shiny = datos["sprites"]["front_shiny"]
        tipos = [t["type"]["name"] for t in datos["types"]]

        especie = pokeapi.obtener_especie(nombre_pokemon)
        descripcion = pokemon.obtener_descripcion(nombre_pokemon)
        grupos_huevo = [g["name"] for g in especie["egg_groups"]]

        cadena_evolutiva = pokemon.obtener_cadena_evolutiva(nombre_pokemon)
        resist_debil = pokemon.calcular_resistencias_y_debilidades(tipos)
        ubicaciones = pokemon.obtener_ubicaciones_por_juego(nombre_pokemon)

        botones_evolucion = []
        for etapa in cadena_evolutiva:
            texto_nivel = f" (Nv. {etapa['nivel']})" if etapa["nivel"] else ""
            botones_evolucion.append(
                ft.TextButton(
                    f"{etapa['nombre']}{texto_nivel}",
                    on_click=lambda e, nombre=etapa["nombre"]: (
                        cerrar_dialogo(),
                        abrir_detalle(nombre),
                    ),
                )
            )

        filas_ubicaciones = []
        if ubicaciones:
            for juego, lugares in ubicaciones.items():
                filas_ubicaciones.append(ft.Text(f"{juego}: {', '.join(lugares)}", size=12))
        else:
            filas_ubicaciones.append(
                ft.Text("No se encuentra en estado salvaje en ningún juego (ej: evoluciones).", size=12)
            )

        contenido_info = ft.Column(
            [
                ft.Row([_badge_tipo(t) for t in tipos]),
                ft.Divider(),
                ft.Text("Descripción", weight=ft.FontWeight.BOLD),
                ft.Text(descripcion, size=13),
                ft.Divider(),
                ft.Text("Ubicaciones", weight=ft.FontWeight.BOLD),
                *filas_ubicaciones,
                ft.Divider(),
                ft.Text("Línea evolutiva", weight=ft.FontWeight.BOLD),
                ft.Row(botones_evolucion, wrap=True),
            ],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
        )

        badges_debilidades = [_badge_tipo(t, f" {m}x") for t, m in resist_debil["debilidades"]]
        badges_resistencias = [_badge_tipo(t, f" {m}x") for t, m in resist_debil["resistencias"]]
        badges_inmunidades = [_badge_tipo(t, " inmune") for t, m in resist_debil["inmunidades"]]

        contenido_detalles = ft.Column(
            [
                ft.Text("Habilidades", weight=ft.FontWeight.BOLD),
                ft.Text(", ".join(habilidades), size=13),
                ft.Text("Grupo(s) huevo", weight=ft.FontWeight.BOLD),
                ft.Text(", ".join(grupos_huevo), size=13),
                ft.Row([
                    ft.Column([ft.Image(src=sprite_normal, width=80, height=80), ft.Text("Normal", size=11)]),
                    ft.Column([ft.Image(src=sprite_shiny, width=80, height=80), ft.Text("Shiny", size=11)]),
                ]),
                ft.Divider(),
                ft.Text("Debilidades", weight=ft.FontWeight.BOLD),
                ft.Row(badges_debilidades, wrap=True) if badges_debilidades else ft.Text("Ninguna", size=12),
                ft.Text("Resistencias", weight=ft.FontWeight.BOLD),
                ft.Row(badges_resistencias, wrap=True) if badges_resistencias else ft.Text("Ninguna", size=12),
                ft.Text("Inmunidades", weight=ft.FontWeight.BOLD),
                ft.Row(badges_inmunidades, wrap=True) if badges_inmunidades else ft.Text("Ninguna", size=12),
                ft.Divider(),
                ft.Text("Stats base", weight=ft.FontWeight.BOLD),
                construir_grafico_stats(stats),
            ],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
        )

        # ft.Tabs cambió de estructura en esta versión de Flet: ahora el
        # título de cada pestaña va en un TabBar, y el contenido de cada
        # una va aparte, en un TabBarView -- los dos adentro de un Column.
        pestañas = ft.Tabs(
            length=2,
            selected_index=0,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Info"),
                            ft.Tab(label="Detalles"),
                        ],
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            contenido_info,
                            contenido_detalles,
                        ],
                    ),
                ],
            ),
        )

        dialogo = ft.AlertDialog(
            title=ft.Text(f"#{datos['id']} {nombre_pokemon.capitalize()}"),
            content=ft.Container(content=pestañas, width=320, height=420),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo())],
        )

        def cerrar_dialogo():
            dialogo.open = False
            page.update()

        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    # --- Tarjetas de la grilla (el click hace una cosa u otra según el modo) ---

    def armar_tarjeta(item):
        sprite_url = pokeapi.sprite_url_por_id(item["id"])

        def al_tocar(e, nombre=item["nombre"]):
            if modo_seleccion:
                abrir_seleccion(nombre)
            else:
                abrir_detalle(nombre)

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
            on_click=al_tocar,
            border_radius=10,
            padding=6,
            ink=True,
            border=ft.Border.all(1, ft.Colors.GREY_300),
        )

    def dibujar_grilla():
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
        campo_busqueda.value = ""
        dropdown_tipo.value = "todos"
        dropdown_generacion.value = "todas"
        dropdown_orden.value = "numero_asc"
        estado["lista_actual"] = pokemon.listar_todos()
        dibujar_grilla()

    def alternar_filtros(e):
        estado["filtros_visibles"] = not estado["filtros_visibles"]
        panel_filtros.visible = estado["filtros_visibles"]
        boton_filtros.text = "Ocultar filtros" if estado["filtros_visibles"] else "Filtros"
        page.update()

    dropdown_tipo.on_change = cambio_tipo
    dropdown_generacion.on_change = cambio_generacion
    dropdown_orden.on_change = cambio_orden

    boton_buscar = ft.ElevatedButton("Buscar", on_click=buscar)
    boton_filtros = ft.OutlinedButton("Filtros", icon=ft.Icons.FILTER_LIST, on_click=alternar_filtros)
    boton_restablecer = ft.TextButton("Restablecer filtros", icon=ft.Icons.REFRESH, on_click=restablecer_filtros)

    panel_filtros = ft.Container(
        content=ft.Column([
            ft.Row([dropdown_tipo, dropdown_generacion, dropdown_orden], wrap=True),
            boton_restablecer,
        ]),
        visible=estado["filtros_visibles"],
        padding=ft.Padding.only(top=10),
    )

    estado["lista_actual"] = pokemon.listar_todos()
    dibujar_grilla()

    # --- Encabezado: distinto según el modo ---

    if modo_seleccion:
        encabezado = ft.Row([
            ft.Text("Elegí un Pokémon", size=24, weight=ft.FontWeight.BOLD),
            ft.TextButton("Cancelar", on_click=lambda e: on_cancelar_seleccion()),
        ])
    else:
        botones_inicio = []
        if on_crear_equipo:
            botones_inicio.append(ft.ElevatedButton("Crear equipo", on_click=lambda e: on_crear_equipo()))
        if on_ver_equipos:
            botones_inicio.append(ft.ElevatedButton("Ver equipos", on_click=lambda e: on_ver_equipos()))

        encabezado = ft.Column([
            ft.Text("Pokédex", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(botones_inicio) if botones_inicio else ft.Container(),
        ])

    return ft.Column(
        [
            encabezado,
            ft.Row([campo_busqueda, boton_buscar, boton_filtros]),
            panel_filtros,
            texto_estado,
            grilla_resultados,
        ],
        expand=True,
    )