# Archivo: database.py
# Maneja la base de datos local (SQLite) que vive en el dispositivo del usuario.
# Acá viven 3 tablas:
#   1. pokemon_cache   -> lo que ya trajimos de PokeAPI, para no pedirlo de nuevo
#   2. equipos         -> los equipos que arma el usuario
#   3. equipo_pokemon  -> cada Pokémon dentro de un equipo, con sus datos elegidos

import sqlite3
import json
import os

# os.path.dirname(__file__) devuelve la carpeta donde está ESTE archivo (database.py).
# os.path.join la combina con el nombre del archivo de la base, así el .db
# siempre queda al lado del script, sin importar desde dónde corras la app.
RUTA_DB = os.path.join(os.path.dirname(__file__), "team_builder.db")


def conectar():
    """
    Abre y devuelve una conexión a la base de datos.
    Cada función que necesite leer o escribir va a llamar a esta función
    primero, para no repetir sql.connect(...) en todos lados.
    """
    conexion = sqlite3.connect(RUTA_DB)

    # Por defecto, sqlite3 devuelve cada fila como una tupla sin nombres,
    # ej: (1, "Garchomp", "Levitación") — tenés que saber de memoria que la
    # posición 1 es el nombre. Con row_factory = sqlite3.Row, podés acceder
    # a cada valor por el nombre de su columna, ej: fila["nombre"] — mucho
    # más legible y menos propenso a errores si cambiás el orden de columnas.
    conexion.row_factory = sqlite3.Row

    return conexion


def inicializar_db():
    """
    Crea las 3 tablas si todavía no existen.
    Se llama UNA SOLA VEZ, al arrancar la app (ya la estás llamando desde
    main.py). Gracias a "IF NOT EXISTS", podés llamarla las veces que
    quieras sin que rompa si las tablas ya estaban creadas.
    """
    conexion = conectar()
    cursor = conexion.cursor()  # el cursor es el que realmente ejecuta el SQL

    # --- Tabla 1: pokemon_cache ---
    # Guarda cada Pokémon que ya trajimos de PokeAPI, como texto JSON.
    # "nombre" es la PRIMARY KEY directamente (no necesita un id aparte,
    # porque el nombre de un Pokémon ya es único por sí solo).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pokemon_cache (
            nombre TEXT PRIMARY KEY,
            datos_json TEXT
        )
    """)

    # --- Tabla 2: equipos ---
    # Cada fila es un equipo del usuario. "id" se autogenera solo
    # (AUTOINCREMENT), no hace falta que lo asignes vos al insertar.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            juego TEXT
        )
    """)

    # --- Tabla 3: equipo_pokemon ---
    # Cada fila es "un Pokémon dentro de un equipo específico".
    # La columna equipo_id es la que conecta esta tabla con la tabla
    # "equipos" de arriba: guarda el id del equipo al que pertenece
    # este Pokémon. La línea FOREIGN KEY le dice a SQLite que ese
    # equipo_id tiene que corresponder a un id real de la tabla equipos
    # (esto se llama "relación" entre tablas).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipo_pokemon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER,
            pokemon_nombre TEXT,
            habilidad TEXT,
            evs_json TEXT,
            FOREIGN KEY (equipo_id) REFERENCES equipos (id)
        )
    """)

    # Hasta acá, todo lo que hicimos con cursor.execute() está "en el aire".
    # commit() confirma los cambios y los guarda de verdad en el archivo .db.
    conexion.commit()

    # Cerramos la conexión para liberar el archivo.
    conexion.close()


def guardar_en_cache(nombre_pokemon, datos):
    """
    Guarda (o actualiza) los datos de un Pokémon en la tabla pokemon_cache.
    'datos' es un diccionario de Python (lo que devuelve pokeapi.py) —
    lo convertimos a texto con json.dumps() porque SQLite no puede guardar
    un diccionario directamente en una columna TEXT.
    """
    conexion = conectar()

    # INSERT OR REPLACE: si ya existe una fila con ese "nombre" (la PRIMARY
    # KEY), la reemplaza en vez de tirar error por clave duplicada.
    conexion.execute(
        "INSERT OR REPLACE INTO pokemon_cache (nombre, datos_json) VALUES (?, ?)",
        (nombre_pokemon.lower(), json.dumps(datos, ensure_ascii=False)),
    )

    conexion.commit()
    conexion.close()


def obtener_de_cache(nombre_pokemon):
    """
    Busca un Pokémon en la caché local.
    Devuelve el diccionario con sus datos si ya estaba guardado,
    o None si todavía no lo consultamos nunca (y hay que pedirlo a la API).
    """
    conexion = conectar()

    # El "?" es un espacio reservado: SQLite mete ahí el valor de forma
    # segura, en vez de armar el texto SQL pegando el nombre directamente
    # (evita bugs y problemas de seguridad si el nombre tuviera caracteres raros).
    fila = conexion.execute(
        "SELECT datos_json FROM pokemon_cache WHERE nombre = ?",
        (nombre_pokemon.lower(),),
    ).fetchone()  # fetchone() trae una sola fila (o None si no encontró nada)

    conexion.close()

    if fila is None:
        return None

    # Convertimos el texto JSON guardado de vuelta a un diccionario de Python.
    return json.loads(fila["datos_json"])


def crear_equipo(nombre, juego):
    """
    Crea un equipo nuevo (vacío, sin Pokémon todavía) y devuelve su id,
    para que después puedas agregarle Pokémon con agregar_pokemon_a_equipo().
    """
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "INSERT INTO equipos (nombre, juego) VALUES (?, ?)",
        (nombre, juego),
    )

    # cursor.lastrowid nos da el id que SQLite le asignó automáticamente
    # a la fila que acabamos de insertar (gracias a AUTOINCREMENT).
    id_equipo_nuevo = cursor.lastrowid

    conexion.commit()
    conexion.close()

    return id_equipo_nuevo


def agregar_pokemon_a_equipo(equipo_id, pokemon_nombre, habilidad, evs):
    """
    Agrega un Pokémon a un equipo ya existente.
    'evs' es un diccionario (ej: {"PS": 4, "Atq": 63, ...}) que convertimos
    a texto igual que hicimos con los datos del Pokémon en guardar_en_cache().
    """
    conexion = conectar()

    conexion.execute(
        """
        INSERT INTO equipo_pokemon (equipo_id, pokemon_nombre, habilidad, evs_json)
        VALUES (?, ?, ?, ?)
        """,
        (equipo_id, pokemon_nombre, habilidad, json.dumps(evs, ensure_ascii=False)),
    )

    conexion.commit()
    conexion.close()


def obtener_equipos():
    """Devuelve la lista de todos los equipos guardados (sin sus Pokémon todavía)."""
    conexion = conectar()

    filas = conexion.execute("SELECT * FROM equipos").fetchall()  # fetchall() trae TODAS las filas

    conexion.close()

    return filas


def obtener_pokemon_de_equipo(equipo_id):
    """
    Devuelve todos los Pokémon que pertenecen a un equipo específico.
    Este es el ejemplo más claro de cómo se usa la relación entre tablas:
    filtramos equipo_pokemon por el equipo_id que apunta al id del equipo pedido.
    """
    conexion = conectar()

    filas = conexion.execute(
        "SELECT * FROM equipo_pokemon WHERE equipo_id = ?",
        (equipo_id,),
    ).fetchall()

    conexion.close()

    return filas