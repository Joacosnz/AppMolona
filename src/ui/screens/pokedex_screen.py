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
#
# Los filtros (búsqueda, tipo 1, tipo 2, generación, juego) se aplican
# TODOS EN CONJUNTO, no uno pisa al otro. La búsqueda es en vivo
# (mientras el usuario escribe, sin botón), tipo 1/tipo 2 son
# indiferentes al orden (planta+veneno = veneno+planta), el filtro de
# "Juego" depende de la generación elegida, y el orden es siempre
# alfabético con un botón para alternar A-Z / Z-A.

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


# Nombres en español de las 6 estadísticas base, para el filtro de
# "Ordenar por > Estadística". La clave es el nombre que usa PokeAPI
# (ver pokeapi.obtener_stats), el valor es lo que se muestra en pantalla.
NOMBRES_STATS = {
    "hp": "HP (Vida)",
    "attack": "Ataque",
    "defense": "Defensa",
    "special-attack": "Ataque Especial",
    "special-defense": "Defensa Especial",
    "speed": "Velocidad",
}

# Si hay más Pokémon que esto en la lista filtrada, no ordenamos por
# estadística: haría falta pedirle a PokeAPI los datos completos de
# cada uno (no solo el nombre), y con la Pokédex casi entera sería
# lentísimo, sobre todo en el celular. Se le pide al usuario que achique
# la lista primero con un filtro de tipo, generación o juego.
LIMITE_ORDEN_POR_ESTADISTICA = 60


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

    # --- Estado de los filtros ---
    # Los filtros por tipo/generación/juego necesitan pedirle algo a
    # PokeAPI, así que guardamos el RESULTADO ya calculado (un conjunto
    # de nombres) en vez de pedirlo de nuevo cada vez que el usuario
    # escribe una letra en el buscador. None significa "sin restricción".
    estado = {
        "filtros_visibles": False,
        "ids_tipo1": None,
        "ids_tipo2": None,
        "ids_generacion": None,
        "ids_juego": None,
        "grupos_por_juego": {},  # version_slug -> grupo_slug, para filtrar_por_juego()
        "orden_ascendente": True,
    }

    def mostrar_error_conexion():
        page.open(
            ft.SnackBar(ft.Text("No se pudo conectar. Revisá tu internet e intentá de nuevo."))
        )

    # --- Controles de filtro y orden ---

    campo_busqueda = ft.TextField(label="Buscar Pokémon", width=200)

    opciones_tipo = [ft.dropdown.Option("todos", "Todos")] + [
        ft.dropdown.Option(t) for t in pokemon.obtener_tipos_disponibles()
    ]

    dropdown_tipo1 = ft.Dropdown(label="Tipo 1", width=150, options=opciones_tipo, value="todos")
    dropdown_tipo2 = ft.Dropdown(label="Tipo 2", width=150, options=opciones_tipo, value="todos")

    dropdown_generacion = ft.Dropdown(
        label="Generación",
        width=170,
        options=[ft.dropdown.Option("todas", "Todas")]
        + [ft.dropdown.Option(g) for g in pokemon.obtener_generaciones_disponibles()],
        value="todas",
    )

    dropdown_juego = ft.Dropdown(
        label="Juego",
        width=200,
        options=[ft.dropdown.Option("todos", "Todos")],
        value="todos",
        disabled=True,  # se habilita al elegir una generación puntual
    )

    # "Número" es el criterio de orden por defecto, de menor a mayor --
    # así la Pokédex arranca siempre mostrando primero al Pokémon #1.
    dropdown_criterio_orden = ft.Dropdown(
        label="Ordenar por",
        width=150,
        options=[
            ft.dropdown.Option("numero", "Número"),
            ft.dropdown.Option("nombre", "Nombre"),
            ft.dropdown.Option("estadistica", "Estadística"),
        ],
        value="numero",
    )

    dropdown_estadistica = ft.Dropdown(
        label="Estadística",
        width=170,
        options=[ft.dropdown.Option(slug, nombre) for slug, nombre in NOMBRES_STATS.items()],
        value="hp",
        visible=False,  # solo se muestra cuando el criterio es "estadistica"
    )

    texto_orden = ft.Text("Ordenar por número (menor a mayor)", size=12)
    boton_orden = ft.IconButton(icon=ft.Icons.ARROW_UPWARD, tooltip="Alternar creciente/decreciente")

    texto_estado = ft.Text("", size=12, color=ft.Colors.GREY)

    grilla_resultados = ft.GridView(
        expand=True, runs_count=3, max_extent=120,
        child_aspect_ratio=0.75, spacing=10, run_spacing=10,
    )

    # --- Cálculo y dibujado de la lista filtrada ---

    def dibujar_grilla(lista):
        grilla_resultados.controls.clear()

        if len(lista) == 0:
            texto_estado.value = "No encontré ningún Pokémon con esos filtros."
        else:
            texto_estado.value = f"{len(lista)} Pokémon"
            for item in lista:
                grilla_resultados.controls.append(armar_tarjeta(item))

        page.update()

    def obtener_valor_stat(nombre_pokemon, campo_stat):
        """Trae (con caché) los datos completos de un Pokémon y devuelve el valor de una stat puntual."""
        datos = pokemon.obtener_pokemon(nombre_pokemon)
        return pokeapi.obtener_stats(datos).get(campo_stat, 0)

    def recalcular_lista():
        """
        Aplica TODOS los filtros activos a la vez (búsqueda + tipo1 +
        tipo2 + generación + juego) sobre la lista completa de Pokémon,
        ordena según el criterio elegido, y redibuja la grilla.
        """
        texto = campo_busqueda.value.strip().lower() if campo_busqueda.value else ""

        resultado = []
        for item in pokemon.listar_todos():
            if texto and texto not in item["nombre"]:
                continue
            if estado["ids_tipo1"] is not None and item["nombre"] not in estado["ids_tipo1"]:
                continue
            if estado["ids_tipo2"] is not None and item["nombre"] not in estado["ids_tipo2"]:
                continue
            if estado["ids_generacion"] is not None and item["nombre"] not in estado["ids_generacion"]:
                continue
            if estado["ids_juego"] is not None and item["nombre"] not in estado["ids_juego"]:
                continue
            resultado.append(item)

        criterio = dropdown_criterio_orden.value
        ascendente = estado["orden_ascendente"]

        if criterio == "numero":
            resultado.sort(key=lambda p: int(p["id"]), reverse=not ascendente)

        elif criterio == "nombre":
            resultado.sort(key=lambda p: p["nombre"], reverse=not ascendente)

        else:  # "estadistica"
            if len(resultado) > LIMITE_ORDEN_POR_ESTADISTICA:
                # Demasiados Pokémon para pedirle los datos completos a
                # cada uno -- mostramos igual la lista (por número, sin
                # pedir nada extra) y avisamos que hay que achicarla.
                resultado.sort(key=lambda p: int(p["id"]))
                dibujar_grilla(resultado)
                texto_estado.value = (
                    f"Son muchos Pokémon ({len(resultado)}) para ordenar por estadística. "
                    "Elegí un tipo, generación o juego primero para achicar la lista."
                )
                page.update()
                return

            campo_stat = dropdown_estadistica.value
            try:
                for item in resultado:
                    item["_valor_stat"] = obtener_valor_stat(item["nombre"], campo_stat)
            except Exception:
                mostrar_error_conexion()
                return

            resultado.sort(key=lambda p: p["_valor_stat"], reverse=not ascendente)

        dibujar_grilla(resultado)

    # --- Cambios de filtro ---

    def cambio_busqueda(e):
        # Búsqueda en vivo: se recalcula con cada letra, sin botón.
        recalcular_lista()

    def cambio_tipo1(e):
        valor = dropdown_tipo1.value
        if valor == "todos":
            estado["ids_tipo1"] = None
        else:
            try:
                resultado = pokemon.filtrar_por_tipo(valor)
            except Exception:
                mostrar_error_conexion()
                return
            estado["ids_tipo1"] = {p["nombre"] for p in resultado}
        recalcular_lista()

    def cambio_tipo2(e):
        valor = dropdown_tipo2.value
        if valor == "todos":
            estado["ids_tipo2"] = None
        else:
            try:
                resultado = pokemon.filtrar_por_tipo(valor)
            except Exception:
                mostrar_error_conexion()
                return
            estado["ids_tipo2"] = {p["nombre"] for p in resultado}
        recalcular_lista()

    def cambio_generacion(e):
        valor = dropdown_generacion.value

        # El filtro de "Juego" depende de la generación elegida, así
        # que lo reseteamos cada vez que cambia la generación.
        dropdown_juego.value = "todos"
        estado["ids_juego"] = None

        if valor == "todas":
            estado["ids_generacion"] = None
            dropdown_juego.options = [ft.dropdown.Option("todos", "Todos")]
            dropdown_juego.disabled = True
            recalcular_lista()
            return

        try:
            resultado = pokemon.filtrar_por_generacion(valor)
            juegos = pokemon.obtener_juegos_de_generacion(valor)
        except Exception:
            mostrar_error_conexion()
            return

        estado["ids_generacion"] = {p["nombre"] for p in resultado}

        estado["grupos_por_juego"] = {j["version_slug"]: j["grupo_slug"] for j in juegos}
        dropdown_juego.options = [ft.dropdown.Option("todos", "Todos")] + [
            ft.dropdown.Option(j["version_slug"], j["nombre"]) for j in juegos
        ]
        dropdown_juego.disabled = False

        recalcular_lista()

    def cambio_juego(e):
        valor = dropdown_juego.value
        if valor == "todos":
            estado["ids_juego"] = None
        else:
            grupo_slug = estado["grupos_por_juego"].get(valor)
            try:
                resultado = pokemon.filtrar_por_juego(grupo_slug)
            except Exception:
                mostrar_error_conexion()
                return
            estado["ids_juego"] = {p["nombre"] for p in resultado}
        recalcular_lista()

    def actualizar_texto_orden():
        direccion = "menor a mayor" if estado["orden_ascendente"] else "mayor a menor"
        criterio = dropdown_criterio_orden.value

        if criterio == "numero":
            texto_orden.value = f"Ordenar por número ({direccion})"
        elif criterio == "nombre":
            etiqueta = "A-Z" if estado["orden_ascendente"] else "Z-A"
            texto_orden.value = f"Ordenar por nombre ({etiqueta})"
        else:
            nombre_stat = NOMBRES_STATS.get(dropdown_estadistica.value, dropdown_estadistica.value)
            texto_orden.value = f"Ordenar por {nombre_stat} ({direccion})"

    def cambio_criterio_orden(e):
        dropdown_estadistica.visible = dropdown_criterio_orden.value == "estadistica"
        actualizar_texto_orden()
        recalcular_lista()

    def cambio_estadistica(e):
        actualizar_texto_orden()
        recalcular_lista()

    def alternar_orden(e):
        estado["orden_ascendente"] = not estado["orden_ascendente"]
        boton_orden.icon = ft.Icons.ARROW_UPWARD if estado["orden_ascendente"] else ft.Icons.ARROW_DOWNWARD
        actualizar_texto_orden()
        recalcular_lista()

    def restablecer_filtros(e):
        """Vuelve todo a su estado original: sin búsqueda ni filtros, orden A-Z."""
        campo_busqueda.value = ""
        dropdown_tipo1.value = "todos"
        dropdown_tipo2.value = "todos"
        dropdown_generacion.value = "todas"
        dropdown_juego.value = "todos"
        dropdown_juego.options = [ft.dropdown.Option("todos", "Todos")]
        dropdown_juego.disabled = True

        dropdown_criterio_orden.value = "numero"
        dropdown_estadistica.value = "hp"
        dropdown_estadistica.visible = False

        estado["ids_tipo1"] = None
        estado["ids_tipo2"] = None
        estado["ids_generacion"] = None
        estado["ids_juego"] = None
        estado["orden_ascendente"] = True
        boton_orden.icon = ft.Icons.ARROW_UPWARD
        actualizar_texto_orden()

        recalcular_lista()

    def alternar_filtros(e):
        estado["filtros_visibles"] = not estado["filtros_visibles"]
        panel_filtros.visible = estado["filtros_visibles"]
        boton_filtros.text = "Ocultar filtros" if estado["filtros_visibles"] else "Filtros"
        page.update()

    campo_busqueda.on_change = cambio_busqueda
    dropdown_tipo1.on_change = cambio_tipo1
    dropdown_tipo2.on_change = cambio_tipo2
    dropdown_generacion.on_change = cambio_generacion
    dropdown_juego.on_change = cambio_juego
    dropdown_criterio_orden.on_change = cambio_criterio_orden
    dropdown_estadistica.on_change = cambio_estadistica
    boton_orden.on_click = alternar_orden

    boton_filtros = ft.OutlinedButton("Filtros", icon=ft.Icons.FILTER_LIST, on_click=alternar_filtros)
    boton_restablecer = ft.TextButton("Restablecer filtros", icon=ft.Icons.REFRESH, on_click=restablecer_filtros)

    panel_filtros = ft.Container(
        content=ft.Column([
            ft.Row([dropdown_tipo1, dropdown_tipo2, dropdown_generacion, dropdown_juego], wrap=True),
            ft.Row([dropdown_criterio_orden, dropdown_estadistica]),
            ft.Row([texto_orden, boton_orden]),
            boton_restablecer,
        ]),
        visible=estado["filtros_visibles"],
        padding=ft.Padding.only(top=10),
    )

    # --- MODO SELECCIÓN: diálogo chico para elegir habilidad y confirmar ---

    def abrir_seleccion(nombre_pokemon):
        try:
            datos = pokemon.obtener_pokemon(nombre_pokemon)
            habilidades = pokeapi.obtener_habilidades(datos)
            sprite = pokeapi.obtener_sprite(datos)
        except Exception:
            mostrar_error_conexion()
            return

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
        try:
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
        except Exception:
            mostrar_error_conexion()
            return

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

    # Al entrar a la pantalla, mostramos TODOS los Pokémon.
    recalcular_lista()

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
            ft.Row([campo_busqueda, boton_filtros]),
            panel_filtros,
            texto_estado,
            grilla_resultados,
        ],
        expand=True,
    )