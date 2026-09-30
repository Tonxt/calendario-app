import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parent.parent / "data" / "calendario.db"


def obtener_conexion():
    return sqlite3.connect(RUTA_BD)


def crear_tablas():
    con = obtener_conexion()
    con.execute("""CREATE TABLE IF NOT EXISTS eventos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT,
        descripcion TEXT,
        aviso_previo_enviado INTEGER DEFAULT 0 NOT NULL,
        aviso_dia_enviado INTEGER DEFAULT 0 NOT NULL
        )""")
    con.commit()
    con.close()
