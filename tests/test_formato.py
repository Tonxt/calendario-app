"""Pruebas de la conversión entre textos del usuario y fechas/horas."""

from datetime import date, time

import pytest

from backend.models import Evento
from interfaz import formato


# --- texto_a_fecha ------------------------------------------------------------
@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("20/10/2026", date(2026, 10, 20)),
        ("  20/10/2026  ", date(2026, 10, 20)),
        ("1/1/2027", date(2027, 1, 1)),
        ("01/01/2027", date(2027, 1, 1)),
        ("20-10-2026", date(2026, 10, 20)),
        ("20/10/26", date(2026, 10, 20)),
        ("29/02/2028", date(2028, 2, 29)),
        ("31/12/9999", date(9999, 12, 31)),
        ("01/01/0001", date(1, 1, 1)),
    ],
)
def test_texto_a_fecha_valido(texto, esperada):
    assert formato.texto_a_fecha(texto) == esperada


@pytest.mark.parametrize(
    "texto",
    [
        "",
        "   ",
        "hola",
        "31/02/2026",
        "29/02/2026",
        "31/04/2026",
        "32/01/2026",
        "00/01/2026",
        "15/13/2026",
        "15/00/2026",
        "2026-10-20",
        "10/20/2026",
        "20/10",
        "20/10/2026 18:30",
        "20/10/20266",
        "20//2026",
        "20.10.2026",
        "-1/10/2026",
        "veinte/diez/2026",
        "20/10/2026; DROP TABLE eventos",
    ],
)
def test_texto_a_fecha_invalido(texto):
    with pytest.raises(ValueError, match="dd/mm/aaaa"):
        formato.texto_a_fecha(texto)


# --- texto_a_hora -------------------------------------------------------------
@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("", None),
        ("   ", None),
        ("18:30", time(18, 30)),
        (" 18:30 ", time(18, 30)),
        ("9:05", time(9, 5)),
        ("9:5", time(9, 5)),
        ("00:00", time(0, 0)),
        ("23:59", time(23, 59)),
        ("18.30", time(18, 30)),
        ("18", time(18, 0)),
        ("7", time(7, 0)),
    ],
)
def test_texto_a_hora_valido(texto, esperada):
    assert formato.texto_a_hora(texto) == esperada


@pytest.mark.parametrize(
    "texto",
    [
        "24:00",
        "25:00",
        "12:60",
        "-1:00",
        "abc",
        "18:30:15",
        "18:",
        ":30",
        "6pm",
        "18 30",
        "18:30hs",
        "1830",
    ],
)
def test_texto_a_hora_invalido(texto):
    with pytest.raises(ValueError, match="hh:mm"):
        formato.texto_a_hora(texto)


# --- de fechas y horas a texto ------------------------------------------------
def test_ida_y_vuelta_de_fecha_y_hora():
    fecha, hora = date(2026, 1, 5), time(9, 5)

    assert formato.texto_a_fecha(formato.fecha_a_texto(fecha)) == fecha
    assert formato.texto_a_hora(formato.hora_a_texto(hora)) == hora


def test_fecha_a_texto_rellena_con_ceros():
    assert formato.fecha_a_texto(date(2026, 1, 5)) == "05/01/2026"


def test_hora_a_texto():
    assert formato.hora_a_texto(time(9, 5)) == "09:05"
    assert formato.hora_a_texto(None) == ""


@pytest.mark.parametrize(
    "fecha, esperado",
    [
        (date(2026, 10, 5), "Lunes 5 de octubre de 2026"),
        (date(2026, 10, 11), "Domingo 11 de octubre de 2026"),
        (date(2028, 2, 29), "Martes 29 de febrero de 2028"),
        (date(2027, 1, 1), "Viernes 1 de enero de 2027"),
    ],
)
def test_fecha_larga(fecha, esperado):
    assert formato.fecha_larga(fecha) == esperado


@pytest.mark.parametrize(
    "anio, mes, esperado",
    [
        (2026, 1, "Enero 2026"),
        (2026, 12, "Diciembre 2026"),
        (2027, 9, "Septiembre 2027"),
    ],
)
def test_titulo_mes(anio, mes, esperado):
    assert formato.titulo_mes(anio, mes) == esperado


def test_resumen_evento():
    con_hora = Evento("Dentista", date(2030, 1, 1), hora=time(10, 30))
    sin_hora = Evento("Cumpleaños", date(2030, 1, 1))

    assert formato.resumen_evento(con_hora) == "10:30 Dentista"
    assert formato.resumen_evento(sin_hora) == "Cumpleaños"


# --- recortar -----------------------------------------------------------------
@pytest.mark.parametrize(
    "texto, maximo, esperado",
    [
        ("Dentista", 20, "Dentista"),
        ("Dentista", 8, "Dentista"),
        ("Dentista", 7, "Dentis…"),
        ("Dentista", 2, "D…"),
        ("Dentista", 1, "…"),
        ("Dentista", 0, ""),
        ("Dentista", -5, ""),
        ("", 5, ""),
        ("Ir al médico", 4, "Ir…"),
    ],
)
def test_recortar(texto, maximo, esperado):
    assert formato.recortar(texto, maximo) == esperado


@pytest.mark.parametrize("maximo", range(0, 30))
def test_recortar_nunca_supera_el_maximo(maximo):
    assert len(formato.recortar("Entrega del trabajo práctico", maximo)) <= maximo
