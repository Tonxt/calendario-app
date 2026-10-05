"""Preparación compartida por todas las pruebas.

pytest carga este archivo solo. Las funciones marcadas con @pytest.fixture
son "fixtures": piezas de preparación que una prueba pide con solo poner su
nombre como parámetro.
"""

from datetime import date, timedelta

import pytest

from backend import database, repository
from backend.models import Evento

# Se guarda antes de que ninguna prueba la reemplace por una temporal.
RUTA_BD_REAL = database.RUTA_BD


@pytest.fixture(autouse=True)
def bd_temporal(tmp_path, monkeypatch):
    """Cada prueba usa una base de datos propia, vacía y descartable.

    autouse=True hace que se aplique a TODAS las pruebas sin pedirla: así
    ninguna puede tocar por error data/calendario.db, la base real.
    """
    ruta = tmp_path / "prueba.db"
    monkeypatch.setattr(database, "RUTA_BD", ruta)
    database.crear_tablas()
    return ruta


@pytest.fixture
def hoy():
    return date.today()


@pytest.fixture
def manana(hoy):
    return hoy + timedelta(days=1)


@pytest.fixture
def ayer(hoy):
    return hoy - timedelta(days=1)


@pytest.fixture
def guardar_evento(hoy):
    """Devuelve una función para crear eventos directamente en la base.

    Va por el repository y no por el service para poder preparar casos que
    el service no permite crear, como eventos en fechas pasadas.
    """

    def _guardar(nombre="Evento", dias=1, **datos):
        evento = Evento(nombre, hoy + timedelta(days=dias), **datos)
        return repository.guardar(evento)

    return _guardar


def contar_eventos() -> int:
    con = database.obtener_conexion()
    cantidad = con.execute("SELECT COUNT(*) FROM eventos").fetchone()[0]
    con.close()
    return cantidad
