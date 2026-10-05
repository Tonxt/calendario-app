"""Pruebas de las reglas del negocio (service)."""

from datetime import date, datetime, time, timedelta

import pytest

from backend import repository, service
from backend.models import Evento
from backend.service import NOMBRE_MAXIMO, ErrorValidacion
from tests.conftest import contar_eventos


# --- crear_evento: casos válidos ----------------------------------------------
def test_crear_evento_lo_guarda_y_le_asigna_id(manana):
    evento = service.crear_evento(Evento("Dentista", manana, hora=time(10, 30)))

    assert evento.id is not None
    assert vars(repository.buscar_por_id(evento.id)) == vars(evento)


def test_se_puede_crear_un_evento_para_hoy(hoy):
    # Límite de la regla "no en el pasado": hoy todavía es válido.
    assert service.crear_evento(Evento("Hoy", hoy)).id is not None


@pytest.mark.parametrize(
    "fecha",
    [date(2028, 2, 29), date(9999, 12, 31)],
    ids=["29_de_febrero_bisiesto", "ultima_fecha_posible"],
)
def test_se_puede_crear_en_fechas_futuras_limite(fecha):
    assert service.crear_evento(Evento("x", fecha)).id is not None


def test_crear_recorta_los_espacios_del_nombre(manana):
    evento = service.crear_evento(Evento("  \t Dentista \n ", manana))

    assert repository.buscar_por_id(evento.id).nombre == "Dentista"


def test_nombre_con_exactamente_el_maximo_de_letras(manana):
    evento = service.crear_evento(Evento("a" * NOMBRE_MAXIMO, manana))

    assert len(repository.buscar_por_id(evento.id).nombre) == NOMBRE_MAXIMO


def test_el_limite_del_nombre_se_mide_despues_de_recortar_espacios(manana):
    nombre = "  " + "a" * NOMBRE_MAXIMO + "  "

    assert service.crear_evento(Evento(nombre, manana)).id is not None


@pytest.mark.parametrize(
    "nombre",
    [
        "x'); DROP TABLE eventos; --",
        "日本語 🎉",
        "<script>alert(1)</script>",
        "O'Brien",
    ],
)
def test_nombres_con_caracteres_especiales_son_validos(manana, nombre):
    evento = service.crear_evento(Evento(nombre, manana))

    assert repository.buscar_por_id(evento.id).nombre == nombre


@pytest.mark.parametrize("descripcion", ["", "   ", "\n\t "])
def test_descripcion_vacia_se_guarda_como_none(manana, descripcion):
    evento = service.crear_evento(Evento("x", manana, descripcion=descripcion))

    assert repository.buscar_por_id(evento.id).descripcion is None


def test_un_evento_nuevo_siempre_arranca_sin_avisos_enviados(manana):
    # Aunque el objeto llegue con los avisos en True, en la base quedan en 0:
    # el objeto y la base no pueden decir cosas distintas.
    evento = service.crear_evento(
        Evento("x", manana, aviso_previo_enviado=True, aviso_dia_enviado=True)
    )

    assert evento.aviso_previo_enviado is False
    assert evento.aviso_dia_enviado is False
    assert repository.buscar_por_id(evento.id).aviso_previo_enviado is False


def test_se_pueden_crear_dos_eventos_iguales(manana):
    # No hay regla contra duplicados: dos turnos con el mismo nombre son válidos.
    uno = service.crear_evento(Evento("Gimnasio", manana, hora=time(8, 0)))
    otro = service.crear_evento(Evento("Gimnasio", manana, hora=time(8, 0)))

    assert uno.id != otro.id


# --- crear_evento: casos inválidos --------------------------------------------
@pytest.mark.parametrize(
    "nombre",
    ["", " ", "\t\n  ", None, 123, 4.5, ["lista"], b"bytes", True],
    ids=[
        "vacio",
        "espacio",
        "solo_blancos",
        "none",
        "entero",
        "decimal",
        "lista",
        "bytes",
        "bool",
    ],
)
def test_nombre_invalido(manana, nombre):
    with pytest.raises(ErrorValidacion):
        service.crear_evento(Evento(nombre, manana))

    assert contar_eventos() == 0


def test_nombre_demasiado_largo(manana):
    with pytest.raises(ErrorValidacion, match=str(NOMBRE_MAXIMO)):
        service.crear_evento(Evento("a" * (NOMBRE_MAXIMO + 1), manana))

    assert contar_eventos() == 0


@pytest.mark.parametrize(
    "fecha",
    [
        None,
        "2030-01-01",
        "20/10/2030",
        20301001,
        0,
        datetime(2030, 1, 1, 10, 0),
        time(10, 0),
        (2030, 1, 1),
    ],
    ids=[
        "none",
        "texto_iso",
        "texto_latino",
        "entero",
        "cero",
        "datetime",
        "time",
        "tupla",
    ],
)
def test_fecha_de_tipo_invalido(fecha):
    with pytest.raises(ErrorValidacion, match="fecha"):
        service.crear_evento(Evento("x", fecha))

    assert contar_eventos() == 0


@pytest.mark.parametrize("dias_atras", [1, 30, 365, 100_000])
def test_fecha_en_el_pasado(hoy, dias_atras):
    with pytest.raises(ErrorValidacion, match="pasado"):
        service.crear_evento(Evento("x", hoy - timedelta(days=dias_atras)))

    assert contar_eventos() == 0


@pytest.mark.parametrize(
    "hora",
    ["10:30", 10, 10.5, datetime(2030, 1, 1, 10, 0), date(2030, 1, 1), (10, 30), False],
    ids=["texto", "entero", "decimal", "datetime", "date", "tupla", "bool"],
)
def test_hora_de_tipo_invalido(manana, hora):
    with pytest.raises(ErrorValidacion, match="horario"):
        service.crear_evento(Evento("x", manana, hora=hora))

    assert contar_eventos() == 0


@pytest.mark.parametrize("descripcion", [123, ["a"], b"bytes", False])
def test_descripcion_de_tipo_invalido(manana, descripcion):
    with pytest.raises(ErrorValidacion, match="descripcion"):
        service.crear_evento(Evento("x", manana, descripcion=descripcion))

    assert contar_eventos() == 0


@pytest.mark.parametrize(
    "no_es_un_evento", [None, "evento", 5, {"nombre": "x"}, Evento]
)
def test_crear_algo_que_no_es_un_evento(no_es_un_evento):
    with pytest.raises(ErrorValidacion):
        service.crear_evento(no_es_un_evento)


def test_crear_un_evento_ya_guardado_no_lo_duplica(manana):
    evento = service.crear_evento(Evento("x", manana))

    with pytest.raises(ErrorValidacion, match="ya fue guardado"):
        service.crear_evento(evento)

    assert contar_eventos() == 1


def test_el_primer_error_que_se_informa_es_el_del_nombre(ayer):
    # Con varios datos mal a la vez, las reglas se revisan en un orden fijo.
    with pytest.raises(ErrorValidacion, match="nombre"):
        service.crear_evento(Evento("", ayer, hora="mal"))


# --- actualizar_evento ---------------------------------------------------------
def test_actualizar_cambia_los_datos(manana):
    evento = service.crear_evento(Evento("Dentista", manana))
    evento.nombre = "Odontólogo"
    evento.hora = time(11, 0)
    evento.descripcion = "Llevar estudios"

    service.actualizar_evento(evento)

    assert vars(repository.buscar_por_id(evento.id)) == vars(evento)


def test_actualizar_sin_cambiar_nada_no_falla(manana):
    evento = service.crear_evento(Evento("x", manana))

    service.actualizar_evento(evento)

    assert vars(repository.buscar_por_id(evento.id)) == vars(evento)


def test_cambiar_la_fecha_resetea_los_dos_avisos(guardar_evento, hoy):
    evento = guardar_evento(dias=1)
    repository.marcar_aviso_previo_enviado(evento.id)
    repository.marcar_aviso_dia_enviado(evento.id)
    evento = repository.buscar_por_id(evento.id)
    evento.fecha = hoy + timedelta(days=7)

    service.actualizar_evento(evento)

    guardado = repository.buscar_por_id(evento.id)
    assert guardado.fecha == hoy + timedelta(days=7)
    assert guardado.aviso_previo_enviado is False
    assert guardado.aviso_dia_enviado is False


def test_cambiar_otros_datos_conserva_los_avisos(guardar_evento):
    evento = guardar_evento(dias=1)
    repository.marcar_aviso_previo_enviado(evento.id)
    evento = repository.buscar_por_id(evento.id)
    evento.nombre = "otro nombre"
    evento.hora = time(9, 0)
    evento.descripcion = "nueva"

    service.actualizar_evento(evento)

    guardado = repository.buscar_por_id(evento.id)
    assert guardado.aviso_previo_enviado is True
    assert guardado.aviso_dia_enviado is False


def test_se_puede_editar_un_evento_pasado_si_no_se_toca_la_fecha(guardar_evento):
    # Punto 1 pedido: antes, corregir la descripción de un evento de ayer
    # fallaba con "la fecha no puede estar en el pasado".
    evento = guardar_evento("Reunión", dias=-10)
    evento.nombre = "Reunión de equipo"
    evento.descripcion = "Se habló del proyecto"

    service.actualizar_evento(evento)

    guardado = repository.buscar_por_id(evento.id)
    assert guardado.nombre == "Reunión de equipo"
    assert guardado.descripcion == "Se habló del proyecto"


def test_un_evento_pasado_se_puede_mover_al_futuro(guardar_evento, manana):
    evento = guardar_evento(dias=-10)
    evento.fecha = manana

    service.actualizar_evento(evento)

    assert repository.buscar_por_id(evento.id).fecha == manana


def test_un_evento_pasado_se_puede_mover_a_hoy(guardar_evento, hoy):
    evento = guardar_evento(dias=-10)
    evento.fecha = hoy

    service.actualizar_evento(evento)

    assert repository.buscar_por_id(evento.id).fecha == hoy


@pytest.mark.parametrize(
    "dias_origen", [5, -10], ids=["evento_futuro", "evento_pasado"]
)
def test_no_se_puede_mover_un_evento_a_una_fecha_pasada(
    guardar_evento, hoy, dias_origen
):
    evento = guardar_evento(dias=dias_origen)
    fecha_original = evento.fecha
    evento.fecha = hoy - timedelta(days=1)

    with pytest.raises(ErrorValidacion, match="pasado"):
        service.actualizar_evento(evento)

    assert repository.buscar_por_id(evento.id).fecha == fecha_original


def test_actualizar_con_datos_invalidos_no_cambia_la_base(manana):
    evento = service.crear_evento(Evento("Original", manana))
    evento.nombre = "   "

    with pytest.raises(ErrorValidacion):
        service.actualizar_evento(evento)

    assert repository.buscar_por_id(evento.id).nombre == "Original"


@pytest.mark.parametrize("fecha", ["2030-01-01", None, datetime(2030, 1, 1)])
def test_actualizar_con_fecha_de_tipo_invalido(manana, fecha):
    evento = service.crear_evento(Evento("x", manana))
    evento.fecha = fecha

    with pytest.raises(ErrorValidacion, match="fecha"):
        service.actualizar_evento(evento)

    assert repository.buscar_por_id(evento.id).fecha == manana


@pytest.mark.parametrize("valor", [1, 0, "si", None])
def test_actualizar_con_avisos_que_no_son_bool(manana, valor):
    evento = service.crear_evento(Evento("x", manana))
    evento.aviso_dia_enviado = valor

    with pytest.raises(ErrorValidacion, match="avisos"):
        service.actualizar_evento(evento)


@pytest.mark.parametrize("id_inexistente", [None, 0, -1, 999_999, "abc"])
def test_actualizar_un_evento_que_no_existe(manana, id_inexistente):
    with pytest.raises(ErrorValidacion, match="no existe"):
        service.actualizar_evento(Evento("x", manana, id=id_inexistente))

    assert contar_eventos() == 0


def test_actualizar_un_evento_que_fue_eliminado(manana):
    evento = service.crear_evento(Evento("x", manana))
    service.eliminar_evento(evento.id)
    evento.nombre = "tarde"

    with pytest.raises(ErrorValidacion, match="no existe"):
        service.actualizar_evento(evento)

    assert contar_eventos() == 0  # no lo "revive"


@pytest.mark.parametrize("no_es_un_evento", [None, "evento", 5])
def test_actualizar_algo_que_no_es_un_evento(no_es_un_evento):
    with pytest.raises(ErrorValidacion):
        service.actualizar_evento(no_es_un_evento)


# --- obtener_evento y eliminar_evento ------------------------------------------
def test_obtener_evento_existente(manana):
    creado = service.crear_evento(Evento("x", manana))

    assert vars(service.obtener_evento(creado.id)) == vars(creado)


@pytest.mark.parametrize("id_inexistente", [None, 0, -1, 999_999, "abc", 1.5, ""])
def test_obtener_evento_inexistente(manana, id_inexistente):
    service.crear_evento(Evento("x", manana))

    with pytest.raises(ErrorValidacion, match="no existe"):
        service.obtener_evento(id_inexistente)


def test_eliminar_evento(manana):
    evento = service.crear_evento(Evento("x", manana))

    service.eliminar_evento(evento.id)

    assert contar_eventos() == 0


def test_eliminar_dos_veces_el_mismo_evento(manana):
    evento = service.crear_evento(Evento("x", manana))
    service.eliminar_evento(evento.id)

    with pytest.raises(ErrorValidacion, match="no existe"):
        service.eliminar_evento(evento.id)


@pytest.mark.parametrize("id_inexistente", [None, 0, -1, 999_999, "abc"])
def test_eliminar_un_evento_inexistente_no_borra_nada(manana, id_inexistente):
    service.crear_evento(Evento("x", manana))

    with pytest.raises(ErrorValidacion, match="no existe"):
        service.eliminar_evento(id_inexistente)

    assert contar_eventos() == 1


def test_se_puede_eliminar_un_evento_pasado(guardar_evento):
    evento = guardar_evento(dias=-30)

    service.eliminar_evento(evento.id)

    assert contar_eventos() == 0


# --- eventos_del_dia ------------------------------------------------------------
def test_eventos_del_dia(guardar_evento, hoy):
    guardar_evento("tarde", dias=0, hora=time(18, 0))
    guardar_evento("mañana", dias=0, hora=time(9, 0))
    guardar_evento("otro día", dias=1)

    nombres = [evento.nombre for evento in service.eventos_del_dia(hoy)]

    assert nombres == ["mañana", "tarde"]


def test_eventos_del_dia_tambien_muestra_dias_pasados(guardar_evento, ayer):
    guardar_evento("ayer", dias=-1)

    assert len(service.eventos_del_dia(ayer)) == 1


@pytest.mark.parametrize("fecha", [None, "2030-01-01", 5, datetime(2030, 1, 1, 0, 0)])
def test_eventos_del_dia_con_fecha_invalida(fecha):
    with pytest.raises(ErrorValidacion, match="fecha"):
        service.eventos_del_dia(fecha)


# --- eventos_del_mes ------------------------------------------------------------
def test_eventos_del_mes_incluye_el_primer_y_el_ultimo_dia():
    for fecha in [
        date(2030, 2, 28),
        date(2030, 3, 1),
        date(2030, 3, 31),
        date(2030, 4, 1),
    ]:
        repository.guardar(Evento(str(fecha), fecha))

    fechas = [evento.fecha for evento in service.eventos_del_mes(2030, 3)]

    assert fechas == [date(2030, 3, 1), date(2030, 3, 31)]


@pytest.mark.parametrize(
    "anio, ultimo_dia",
    [(2028, 29), (2027, 28), (2100, 28), (2000, 29)],
    ids=["bisiesto", "comun", "siglo_no_bisiesto", "siglo_bisiesto"],
)
def test_eventos_del_mes_en_febrero(anio, ultimo_dia):
    repository.guardar(Evento("fin de febrero", date(anio, 2, ultimo_dia)))
    repository.guardar(Evento("marzo", date(anio, 3, 1)))

    eventos = service.eventos_del_mes(anio, 2)

    assert [evento.nombre for evento in eventos] == ["fin de febrero"]


def test_eventos_del_mes_en_diciembre_no_trae_enero():
    repository.guardar(Evento("31 dic", date(2030, 12, 31)))
    repository.guardar(Evento("1 ene", date(2031, 1, 1)))

    eventos = service.eventos_del_mes(2030, 12)

    assert [evento.nombre for evento in eventos] == ["31 dic"]


def test_eventos_del_mes_no_mezcla_el_mismo_mes_de_otro_anio():
    repository.guardar(Evento("2030", date(2030, 5, 10)))
    repository.guardar(Evento("2031", date(2031, 5, 10)))

    assert [evento.nombre for evento in service.eventos_del_mes(2031, 5)] == ["2031"]


def test_eventos_del_mes_vacio():
    assert service.eventos_del_mes(2030, 1) == []


@pytest.mark.parametrize(
    "anio, mes", [(1, 1), (9999, 12)], ids=["primer_mes", "ultimo_mes"]
)
def test_eventos_del_mes_en_los_limites_del_calendario(anio, mes):
    assert service.eventos_del_mes(anio, mes) == []


@pytest.mark.parametrize(
    "anio, mes",
    [
        (2030, 0),
        (2030, 13),
        (2030, -1),
        (0, 1),
        (10_000, 1),
        (-2030, 1),
        ("2030", 5),
        (2030, "5"),
        (2030, 5.0),
        (None, None),
        (2030, True),
    ],
)
def test_eventos_del_mes_con_valores_invalidos(anio, mes):
    with pytest.raises(ErrorValidacion, match="mes"):
        service.eventos_del_mes(anio, mes)
