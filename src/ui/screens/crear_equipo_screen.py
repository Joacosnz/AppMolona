# Archivo: crear_equipo_screen.py (dentro de ui/screens/)
# Pantalla para armar un equipo nuevo: TODO en una sola pantalla -- el
# nombre del equipo, el juego, y los 6 "slots" circulares (uno por cada
# lugar del equipo) están siempre visibles juntos.
#
# Los slots vacíos muestran un "+"; al tocarlos, esta pantalla se hace a
# un lado y se abre la Pokédex COMPLETA (pokedex_screen.py) en "modo
# selección": ahí el usuario busca/filtra como en la Pokédex normal, y
# al elegir un Pokémon (con su habilidad) se vuelve automáticamente acá,
# con ese slot ya cargado.
#
# El equipo puede quedar incompleto -- no hace falta llenar los 6 slots.
#
# Si el usuario toca "Volver al menú" y tiene cambios sin guardar, se le
# pregunta si quiere guardar, descartar, o seguir editando.

import flet as ft

from data import database
from ui.screens import pokedex_screen


def build(page: ft.Page, volver_al_menu):
    """
    Arma y devuelve el contenido de la pantalla de "Crear equipo".

    'volver_al_menu' es la función que nos pasa main.py para volver a
    la pantalla de inicio.
    """

    # --- Estado de la pantalla ---
    # slots: lista de 6 posiciones. Cada una es None (vacía) o un
    # diccionario {"nombre": ..., "habilidad": ..., "sprite": ...}.
    slots = [None, None, None, None, None, None]

    campo_nombre_equipo = ft.TextField(label="Nombre del equipo", width=280)
    campo_juego = ft.TextField(label="Juego (ej: Rubí y Zafiro)", width=280)
    texto_error = ft.Text("", color=ft.Colors.RED, size=12)

    grilla_slots = ft.GridView(
        runs_count=3,
        max_extent=130,
        child_aspect_ratio=0.9,
        spacing=15,
        run_spacing=15,
        height=300,
    )

    # --- Helpers generales ---

    def hay_cambios_sin_guardar():
        """True si hay algo que se perdería si el usuario sale sin guardar."""
        return bool(campo_nombre_equipo.value) or bool(campo_juego.value) or any(
            s is not None for s in slots
        )

    def volver_a_esta_pantalla():
        """
        Vuelve a mostrar ESTA misma pantalla de "Crear equipo" (con todo
        lo que el usuario ya cargó), después de haber ido a la Pokédex
        a elegir un Pokémon. No reconstruye nada -- reusa 'raiz', el
        árbol de controles que ya armamos más abajo.
        """
        page.controls.clear()
        page.add(raiz)
        page.update()

    # --- Slots: dibujado ---

    def armar_slot(indice):
        """
        Arma el círculo visual de un slot puntual, según si está vacío
        o ya tiene un Pokémon cargado.
        """
        contenido_slot = slots[indice]

        if contenido_slot is None:
            interior = ft.Column(
                [ft.Icon(ft.Icons.ADD, size=32, color=ft.Colors.GREY_400)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            borde = ft.Border.all(2, ft.Colors.GREY_500)
        else:
            interior = ft.Column(
                [
                    ft.Image(
                        src=contenido_slot["sprite"],
                        width=60,
                        height=60,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    ft.Text(
                        contenido_slot["nombre"],
                        size=11,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=1,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            )
            borde = ft.Border.all(2, ft.Colors.BLUE_300)

        return ft.Container(
            content=interior,
            width=110,
            height=110,
            border_radius=55,
            border=borde,
            ink=True,
            alignment=ft.Alignment.CENTER,
            on_click=lambda e, i=indice: click_slot(i),
        )

    def redibujar_slots():
        grilla_slots.controls = [armar_slot(i) for i in range(6)]
        page.update()

    def click_slot(indice):
        """
        Slot vacío -> vamos directo a la Pokédex a elegir un Pokémon.
        Slot ya ocupado -> preguntamos si lo quiere cambiar o sacarlo,
        antes de mandarlo a la Pokédex de nuevo.
        """
        if slots[indice] is None:
            abrir_pokedex_para_slot(indice)
        else:
            abrir_dialogo_editar_slot(indice)

    def abrir_dialogo_editar_slot(indice):
        def cambiar(e):
            cerrar_dialogo()
            abrir_pokedex_para_slot(indice)

        def quitar(e):
            slots[indice] = None
            cerrar_dialogo()
            redibujar_slots()

        def cerrar_dialogo():
            dialogo.open = False
            page.update()

        dialogo = ft.AlertDialog(
            title=ft.Text(slots[indice]["nombre"].capitalize()),
            content=ft.Text(f"Habilidad actual: {slots[indice]['habilidad']}"),
            actions=[
                ft.ElevatedButton("Cambiar Pokémon", on_click=cambiar),
                ft.TextButton("Quitar del equipo", on_click=quitar),
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo()),
            ],
        )

        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    def abrir_pokedex_para_slot(indice):
        """
        Reemplaza esta pantalla por la Pokédex completa, en modo
        selección, para elegir el Pokémon (y su habilidad) de este slot.
        """

        def al_elegir_pokemon(nombre, habilidad, sprite):
            slots[indice] = {"nombre": nombre, "habilidad": habilidad, "sprite": sprite}
            volver_a_esta_pantalla()
            redibujar_slots()

        page.controls.clear()
        page.add(
            pokedex_screen.build(
                page,
                modo_seleccion=True,
                on_pokemon_elegido=al_elegir_pokemon,
                on_cancelar_seleccion=volver_a_esta_pantalla,
            )
        )
        page.update()

    # --- Guardar equipo ---

    def intentar_guardar(e=None):
        """
        Valida y guarda el equipo en la base. Se usa tanto desde el
        botón "Guardar equipo" como desde el diálogo de confirmación al
        querer salir sin haber guardado.
        """
        if not campo_nombre_equipo.value:
            texto_error.value = "Ponele un nombre al equipo antes de guardar."
            page.update()
            return

        pokemon_cargados = [s for s in slots if s is not None]

        if len(pokemon_cargados) == 0:
            texto_error.value = "Agregá al menos un Pokémon antes de guardar."
            page.update()
            return

        id_equipo = database.crear_equipo(campo_nombre_equipo.value, campo_juego.value)

        # Los EVs arrancan todos en 0 -- se editan después, en la
        # pantalla de edición (igual que en tu CLI original).
        evs_iniciales = {"PS": 0, "Atq": 0, "Def": 0, "Atq_Esp": 0, "Def_Esp": 0, "Vel": 0}

        for p in pokemon_cargados:
            database.agregar_pokemon_a_equipo(id_equipo, p["nombre"], p["habilidad"], evs_iniciales)

        volver_al_menu()

    # --- Volver al menú, con confirmación si hay cambios sin guardar ---

    def click_volver_al_menu(e):
        if not hay_cambios_sin_guardar():
            volver_al_menu()
            return

        def guardar_y_salir(e):
            cerrar_confirmacion(e)
            intentar_guardar()

        def salir_sin_guardar(e):
            cerrar_confirmacion(e)
            volver_al_menu()

        def cerrar_confirmacion(e):
            dialogo_confirmacion.open = False
            page.update()

        dialogo_confirmacion = ft.AlertDialog(
            title=ft.Text("¿Salir sin guardar?"),
            content=ft.Text("Tenés cambios sin guardar en este equipo. ¿Qué querés hacer?"),
            actions=[
                ft.TextButton("Guardar y salir", on_click=guardar_y_salir),
                ft.TextButton("Salir sin guardar", on_click=salir_sin_guardar),
                ft.TextButton("Seguir editando", on_click=cerrar_confirmacion),
            ],
        )

        page.overlay.append(dialogo_confirmacion)
        dialogo_confirmacion.open = True
        page.update()

    # --- Armado de la pantalla completa ---

    redibujar_slots()

    raiz = ft.Column(
        [
            ft.Text("Crear equipo", size=24, weight=ft.FontWeight.BOLD),
            campo_nombre_equipo,
            campo_juego,
            ft.Divider(),
            ft.Text(
                "Tocá un espacio vacío para agregar un Pokémon. No hace falta llenarlos todos.",
                size=12,
                color=ft.Colors.GREY,
            ),
            grilla_slots,
            texto_error,
            ft.Row(
                [
                    ft.TextButton("Volver al menú", on_click=click_volver_al_menu),
                    ft.ElevatedButton("Guardar equipo", on_click=intentar_guardar),
                ]
            ),
        ]
    )

    return raiz