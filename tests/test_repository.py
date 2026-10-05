"""Pruebas del acceso a datos (guardar, buscar, actualizar, eliminar y avisos)."""

from datetime import date, time, timedelta

import pytest

from backend import database, repository
from backend.models import Evento
from tests.conftest import contar_eventos


# --- guardar y buscar_por_id --------------------------------------------------
def test_guardar_asigna_ids_consecutivos(guardar_evento):
    assert guardar_evento("a").id == 1
    assert guardar_evento("b").id == 2
    assert guardar_evento("c").id == 3


def test_guardar_devuelve_el_mismo_objeto_con_su_id(hoy):
    evento = Evento("Dentista", hoy)

    devuelto = repository.guardar(evento)

    assert devuelto is evento
    assert evento.id is not None


def test_ida_y_vuelta_conserva_todos_los_datos_y_sus_tipos(hoy):
    original = repository.guardar(
        Evento("Parcial", hoy, hora=time(18, 30), descripcion="Aula 305")
    )

    leido = repository.buscar_por_id(original.id)

    assert vars(leido) == vars(original)
    assert type(leido.fecha) is date
    assert type(leido.hora) is time
    assert leido.aviso_previo_enviado is False  # bool, no el 0 de SQLite
    assert leido.aviso_dia_enviado is False


def test_evento_sin_hora_ni_descripcion_vuelve_con_none(guardar_evento):
    leido = repository.buscar_por_id(guardar_evento("Cumpleaños").id)

    assert leido.hora is None
    assert leido.descripcion is None


def test_la_fecha_se_guarda_como_texto_iso_con_ceros(bd_temporal):
    repository.guardar(Evento("x", date(2030, 1, 5), hora=time(9, 5)))

    con = database.obtener_conexion()
    fecha, hora = con.execute("SELECT fecha, hora FROM eventos").fetchone()
    con.close()

    assert fecha == "2030-01-05"
    assert hora == "09:05"


@pytest.mark.parametrize(
    "hora",
    [time(0, 0), time(23, 59), time(12, 0)],
    ids=["medianoche", "ultimo_minuto", "mediodia"],
)
def test_horas_limite(hoy, hora):
    evento = repository.guardar(Evento("x", hoy, hora=hora))

    assert repository.buscar_por_id(evento.id).hora == hora


def test_los_segundos_de_la_hora_se_descartan(hoy):
    # Decisión de diseño: la hora se guarda como HH:MM.
    evento = repository.guardar(Evento("x", hoy, hora=time(10, 30, 59, 999)))

    assert repository.buscar_por_id(evento.id).hora == time(10, 30)


@pytest.mark.parametrize(
    "fecha",
    [date(2028, 2, 29), date(1, 1, 1), date(9999, 12, 31), date(2026, 12, 31)],
    ids=["bisiesto", "fecha_minima", "fecha_maxima", "fin_de_anio"],
)
def test_fechas_limite(fecha):
    evento = repository.guardar(Evento("x", fecha))

    assert repository.buscar_por_id(evento.id).fecha == fecha


@pytest.mark.parametrize(
    "nombre",
    [
        "x'); DROP TABLE eventos; --",
        "Robert' OR '1'='1",
        "comillas \"dobles\" y 'simples'",
        "ñandú café ünïcödé 日本語 🎉🎂",
        "línea 1\nlínea 2\ttab",
        "%_?* comodines",
        "a" * 10_000,
        " espacios alrededor ",
    ],
    ids=[
        "inyeccion_drop",
        "inyeccion_or",
        "comillas",
        "unicode_y_emojis",
        "saltos_de_linea",
        "comodines_sql",
        "diez_mil_letras",
        "espacios",
    ],
)
def test_textos_raros_se_guardan_tal_cual(hoy, nombre):
    evento = repository.guardar(Evento(nombre, hoy, descripcion=nombre))

    leido = repository.buscar_por_id(evento.id)

    assert leido.nombre == nombre
    assert leido.descripcion == nombre
    assert contar_eventos() == 1  # la tabla sigue existiendo y con una sola fila


@pytest.mark.parametrize("id_inexistente", [0, -1, 999_999, None, "abc", 2**62])
def test_buscar_por_id_inexistente_devuelve_none(guardar_evento, id_inexistente):
    guardar_evento()

    assert repository.buscar_por_id(id_inexistente) is None


# --- búsquedas por fecha ------------------------------------------------------
def test_buscar_por_fecha_trae_solo_ese_dia(guardar_evento, hoy):
    guardar_evento("ayer", dias=-1)
    guardar_evento("hoy 1", dias=0)
    guardar_evento("hoy 2", dias=0)
    guardar_evento("mañana", dias=1)

    nombres = {evento.nombre for evento in repository.buscar_por_fecha(hoy)}

    assert nombres == {"hoy 1", "hoy 2"}


def test_buscar_por_fecha_sin_eventos_devuelve_lista_vacia(hoy):
    assert repository.buscar_por_fecha(hoy) == []


def test_buscar_por_fecha_ordena_por_hora_y_sin_hora_primero(guardar_evento, hoy):
    guardar_evento("noche", dias=0, hora=time(21, 0))
    guardar_evento("todo el día", dias=0)
    guardar_evento("mañana temprano", dias=0, hora=time(7, 30))
    guardar_evento("mediodía", dias=0, hora=time(12, 0))

    nombres = [evento.nombre for evento in repository.buscar_por_fecha(hoy)]

    assert nombres == ["todo el día", "mañana temprano", "mediodía", "noche"]


def test_buscar_entre_fechas_incluye_los_dos_extremos(guardar_evento, hoy):
    guardar_evento("antes", dias=-1)
    guardar_evento("desde", dias=0)
    guardar_evento("medio", dias=5)
    guardar_evento("hasta", dias=10)
    guardar_evento("después", dias=11)

    eventos = repository.buscar_entre_fechas(hoy, hoy + timedelta(days=10))

    assert [evento.nombre for evento in eventos] == ["desde", "medio", "hasta"]


def test_buscar_entre_fechas_ordena_por_fecha_y_despues_por_hora(guardar_evento, hoy):
    guardar_evento("día 2 tarde", dias=2, hora=time(18, 0))
    guardar_evento("día 1 tarde", dias=1, hora=time(18, 0))
    guardar_evento("día 2 mañana", dias=2, hora=time(8, 0))
    guardar_evento("día 1 sin hora", dias=1)

    eventos = repository.buscar_entre_fechas(hoy, hoy + timedelta(days=3))

    assert [evento.nombre for evento in eventos] == [
        "día 1 sin hora",
        "día 1 tarde",
        "día 2 mañana",
        "día 2 tarde",
    ]


def test_buscar_entre_fechas_de_un_solo_dia(guardar_evento, hoy):
    guardar_evento("único", dias=0)

    assert len(repository.buscar_entre_fechas(hoy, hoy)) == 1


def test_buscar_entre_fechas_con_rango_invertido_no_trae_nada(guardar_evento, hoy):
    guardar_evento("x", dias=1)

    assert repository.buscar_entre_fechas(hoy + timedelta(days=5), hoy) == []


def test_el_orden_por_texto_funciona_entre_anios_y_siglos():
    # Las fechas se comparan como texto: gracias al formato ISO, el orden
    # alfabético coincide con el cronológico incluso al cambiar de año.
    for fecha in [
        date(2027, 1, 1),
        date(2026, 12, 31),
        date(999, 6, 1),
        date(2100, 1, 1),
    ]:
        repository.guardar(Evento(str(fecha), fecha))

    eventos = repository.buscar_entre_fechas(date(1, 1, 1), date(9999, 12, 31))

    assert [evento.fecha for evento in eventos] == [
        date(999, 6, 1),
        date(2026, 12, 31),
        date(2027, 1, 1),
        date(2100, 1, 1),
    ]


# --- actualizar ---------------------------------------------------------------
def test_actualizar_cambia_todos_los_campos_editables(guardar_evento, hoy):
    evento = guardar_evento("viejo", dias=1, hora=time(9, 0), descripcion="vieja")
    evento.nombre = "nuevo"
    evento.fecha = hoy + timedelta(days=20)
    evento.hora = None
    evento.descripcion = None
    evento.aviso_previo_enviado = True
    evento.aviso_dia_enviado = True

    repository.actualizar(evento)

    assert vars(repository.buscar_por_id(evento.id)) == vars(evento)


def test_actualizar_solo_toca_la_fila_del_evento(guardar_evento):
    uno = guardar_evento("uno")
    otro = guardar_evento("otro")
    uno.nombre = "uno cambiado"

    repository.actualizar(uno)

    assert repository.buscar_por_id(otro.id).nombre == "otro"


def test_actualizar_un_evento_inexistente_no_crea_nada(hoy):
    repository.actualizar(Evento("fantasma", hoy, id=123))

    assert contar_eventos() == 0


# --- eliminar -----------------------------------------------------------------
def test_eliminar_borra_solo_ese_evento(guardar_evento):
    uno = guardar_evento("uno")
    otro = guardar_evento("otro")

    repository.eliminar(uno.id)

    assert repository.buscar_por_id(uno.id) is None
    assert repository.buscar_por_id(otro.id) is not None


def test_eliminar_un_id_inexistente_no_falla_ni_borra_otros(guardar_evento):
    guardar_evento()

    repository.eliminar(999)

    assert contar_eventos() == 1


# --- avisos -------------------------------------------------------------------
def test_buscar_avisos_previos_pendientes(guardar_evento, manana):
    pendiente = guardar_evento("pendiente", dias=1)
    enviado = guardar_evento("enviado", dias=1)
    guardar_evento("otro día", dias=2)
    repository.marcar_aviso_previo_enviado(enviado.id)

    eventos = repository.buscar_avisos_previos_pendientes(manana)

    assert [evento.id for evento in eventos] == [pendiente.id]


def test_buscar_avisos_dia_pendientes(guardar_evento, hoy):
    pendiente = guardar_evento("pendiente", dias=0)
    enviado = guardar_evento("enviado", dias=0)
    repository.marcar_aviso_dia_enviado(enviado.id)

    eventos = repository.buscar_avisos_dia_pendientes(hoy)

    assert [evento.id for evento in eventos] == [pendiente.id]


def test_marcar_un_aviso_no_cambia_el_otro(guardar_evento):
    evento = guardar_evento()

    repository.marcar_aviso_previo_enviado(evento.id)

    leido = repository.buscar_por_id(evento.id)
    assert leido.aviso_previo_enviado is True
    assert leido.aviso_dia_enviado is False

    repository.marcar_aviso_dia_enviado(evento.id)

    leido = repository.buscar_por_id(evento.id)
    assert leido.aviso_previo_enviado is True
    assert leido.aviso_dia_enviado is True


def test_marcar_dos_veces_el_mismo_aviso_no_falla(guardar_evento):
    evento = guardar_evento()

    repository.marcar_aviso_dia_enviado(evento.id)
    repository.marcar_aviso_dia_enviado(evento.id)

    assert repository.buscar_por_id(evento.id).aviso_dia_enviado is True


def test_marcar_aviso_de_un_evento_inexistente_no_falla():
    repository.marcar_aviso_previo_enviado(999)
    repository.marcar_aviso_dia_enviado(999)

    assert contar_eventos() == 0


# --- volumen ------------------------------------------------------------------
def test_trescientos_eventos_el_mismo_dia(hoy):
    for numero in range(300):
        repository.guardar(Evento(f"evento {numero}", hoy))

    assert len(repository.buscar_por_fecha(hoy)) == 300
