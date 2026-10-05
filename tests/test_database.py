"""Pruebas de la conexión y de la creación de la tabla."""

import sqlite3
from pathlib import Path

import pytest

from backend import database
from tests.conftest import RUTA_BD_REAL


def columnas_de_eventos() -> dict:
    con = database.obtener_conexion()
    filas = con.execute("PRAGMA table_info(eventos)").fetchall()
    con.close()
    # Cada fila: (posición, nombre, tipo, not_null, valor_por_defecto, es_clave)
    return {fila[1]: fila for fila in filas}


def test_la_tabla_tiene_las_siete_columnas_en_orden():
    con = database.obtener_conexion()
    nombres = [fila[1] for fila in con.execute("PRAGMA table_info(eventos)")]
    con.close()

    assert nombres == [
        "id",
        "nombre",
        "fecha",
        "hora",
        "descripcion",
        "aviso_previo_enviado",
        "aviso_dia_enviado",
    ]


def test_crear_tablas_se_puede_llamar_muchas_veces_sin_perder_datos():
    con = database.obtener_conexion()
    con.execute("INSERT INTO eventos (nombre, fecha) VALUES ('x', '2030-01-01')")
    con.commit()
    con.close()

    for _ in range(3):
        database.crear_tablas()

    con = database.obtener_conexion()
    assert con.execute("SELECT COUNT(*) FROM eventos").fetchone()[0] == 1
    con.close()


def test_crear_tablas_crea_la_carpeta_si_no_existe(tmp_path, monkeypatch):
    ruta = tmp_path / "carpeta" / "que" / "no" / "existe" / "calendario.db"
    monkeypatch.setattr(database, "RUTA_BD", ruta)

    database.crear_tablas()

    assert ruta.exists()


@pytest.mark.parametrize("columna", ["nombre", "fecha"])
def test_nombre_y_fecha_son_obligatorios(columna):
    valores = {"nombre": "x", "fecha": "2030-01-01"}
    valores[columna] = None
    con = database.obtener_conexion()

    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            "INSERT INTO eventos (nombre, fecha) VALUES (?, ?)",
            (valores["nombre"], valores["fecha"]),
        )
    con.close()


@pytest.mark.parametrize("columna", ["aviso_previo_enviado", "aviso_dia_enviado"])
def test_los_avisos_arrancan_en_cero_y_no_aceptan_nulos(columna):
    info = columnas_de_eventos()[columna]
    assert info[3] == 1  # NOT NULL
    assert info[4] == "0"  # DEFAULT 0

    con = database.obtener_conexion()
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            f"INSERT INTO eventos (nombre, fecha, {columna}) VALUES ('x', '2030-01-01', NULL)"
        )
    con.close()


def test_los_ids_no_se_reutilizan_despues_de_borrar():
    con = database.obtener_conexion()
    con.execute("INSERT INTO eventos (nombre, fecha) VALUES ('a', '2030-01-01')")
    con.execute("INSERT INTO eventos (nombre, fecha) VALUES ('b', '2030-01-01')")
    con.execute("DELETE FROM eventos WHERE id = 2")
    cursor = con.execute(
        "INSERT INTO eventos (nombre, fecha) VALUES ('c', '2030-01-01')"
    )
    con.commit()
    con.close()

    assert cursor.lastrowid == 3  # AUTOINCREMENT: el 2 quedó "quemado"


def test_la_ruta_real_es_absoluta_y_apunta_a_data():
    # Se calcula desde la ubicación de database.py, no desde la carpeta en la
    # que está la terminal: por eso tiene que ser absoluta.
    assert RUTA_BD_REAL.is_absolute()
    assert RUTA_BD_REAL.name == "calendario.db"
    assert RUTA_BD_REAL.parent.name == "data"
    assert RUTA_BD_REAL.parent.parent == Path(database.__file__).resolve().parent.parent


def test_las_pruebas_nunca_usan_la_base_real():
    assert database.RUTA_BD != RUTA_BD_REAL
