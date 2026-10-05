"""Pruebas de los recordatorios. No muestran notificaciones reales."""

from datetime import date, time, timedelta

import pytest

from backend import repository, scheduler
from backend.models import Evento


@pytest.fixture
def avisos(monkeypatch):
    """Reemplaza `notificar` por una función que anota cada aviso en una lista."""
    enviados = []
    monkeypatch.setattr(
        scheduler,
        "notificar",
        lambda titulo, mensaje: enviados.append((titulo, mensaje)),
    )
    return enviados


def fijar_hoy(monkeypatch, fecha: date) -> None:
    """Hace que, para el scheduler, hoy sea la fecha indicada."""

    class FechaFija(date):
        @classmethod
        def today(cls):
            return fecha

    monkeypatch.setattr(scheduler, "date", FechaFija)


# --- qué se avisa y cuándo ----------------------------------------------------
def test_sin_eventos_no_avisa_nada(avisos):
    scheduler.revisar_avisos()

    assert avisos == []


def test_evento_de_manana_recibe_el_aviso_previo(avisos, guardar_evento, manana):
    evento = guardar_evento("Dentista", dias=1)

    scheduler.revisar_avisos()

    assert avisos == [("Dentista", f"Mañana, {manana.strftime('%d/%m')}")]
    guardado = repository.buscar_por_id(evento.id)
    assert guardado.aviso_previo_enviado is True
    assert guardado.aviso_dia_enviado is False


def test_evento_de_hoy_recibe_el_aviso_del_dia(avisos, guardar_evento, hoy):
    evento = guardar_evento("Parcial", dias=0)

    scheduler.revisar_avisos()

    assert avisos == [("Parcial", f"Hoy, {hoy.strftime('%d/%m')}")]
    guardado = repository.buscar_por_id(evento.id)
    assert guardado.aviso_dia_enviado is True
    assert guardado.aviso_previo_enviado is False


@pytest.mark.parametrize("dias", [-365, -1, 2, 7, 365])
def test_eventos_de_otros_dias_no_se_avisan(avisos, guardar_evento, dias):
    evento = guardar_evento(dias=dias)

    scheduler.revisar_avisos()

    assert avisos == []
    guardado = repository.buscar_por_id(evento.id)
    assert guardado.aviso_previo_enviado is False
    assert guardado.aviso_dia_enviado is False


def test_la_hora_del_evento_no_influye_en_los_avisos(avisos, guardar_evento):
    guardar_evento("temprano", dias=0, hora=time(0, 0))
    guardar_evento("tarde", dias=0, hora=time(23, 59))

    scheduler.revisar_avisos()

    assert sorted(titulo for titulo, _ in avisos) == ["tarde", "temprano"]


def test_se_avisan_todos_los_eventos_del_mismo_dia(avisos, guardar_evento):
    for numero in range(25):
        guardar_evento(f"evento {numero}", dias=0)

    scheduler.revisar_avisos()

    assert len(avisos) == 25


# --- no repetir ---------------------------------------------------------------
def test_una_segunda_revision_no_repite_los_avisos(avisos, guardar_evento):
    guardar_evento("hoy", dias=0)
    guardar_evento("mañana", dias=1)

    scheduler.revisar_avisos()
    scheduler.revisar_avisos()
    scheduler.revisar_avisos()

    assert len(avisos) == 2


def test_un_aviso_ya_marcado_no_se_envia(avisos, guardar_evento):
    evento = guardar_evento(dias=0)
    repository.marcar_aviso_dia_enviado(evento.id)

    scheduler.revisar_avisos()

    assert avisos == []


# --- el paso de los días -------------------------------------------------------
def test_recorrido_completo_de_un_evento_dia_por_dia(avisos, monkeypatch):
    dia_evento = date(2030, 5, 20)
    evento = repository.guardar(Evento("Final", dia_evento))

    fijar_hoy(monkeypatch, date(2030, 5, 18))  # dos días antes: nada
    scheduler.revisar_avisos()
    assert avisos == []

    fijar_hoy(monkeypatch, date(2030, 5, 19))  # día anterior: aviso previo
    scheduler.revisar_avisos()
    scheduler.revisar_avisos()
    assert avisos == [("Final", "Mañana, 20/05")]

    fijar_hoy(monkeypatch, dia_evento)  # el día: aviso del día
    scheduler.revisar_avisos()
    scheduler.revisar_avisos()
    assert avisos == [("Final", "Mañana, 20/05"), ("Final", "Hoy, 20/05")]

    fijar_hoy(monkeypatch, date(2030, 5, 21))  # al día siguiente: nada más
    scheduler.revisar_avisos()
    assert len(avisos) == 2
    guardado = repository.buscar_por_id(evento.id)
    assert guardado.aviso_previo_enviado is True
    assert guardado.aviso_dia_enviado is True


def test_si_la_compu_estuvo_apagada_el_dia_anterior_solo_llega_el_aviso_del_dia(
    avisos, monkeypatch
):
    repository.guardar(Evento("Final", date(2030, 5, 20)))

    fijar_hoy(monkeypatch, date(2030, 5, 20))  # se prende recién el día del evento
    scheduler.revisar_avisos()

    assert avisos == [("Final", "Hoy, 20/05")]


def test_si_la_compu_estuvo_apagada_varios_dias_no_avisa_eventos_viejos(
    avisos, monkeypatch
):
    repository.guardar(Evento("Viejo", date(2030, 5, 20)))

    fijar_hoy(monkeypatch, date(2030, 5, 25))
    scheduler.revisar_avisos()

    assert avisos == []


@pytest.mark.parametrize(
    "hoy_falso, dia_evento, texto",
    [
        (date(2030, 12, 31), date(2031, 1, 1), "Mañana, 01/01"),
        (date(2028, 2, 28), date(2028, 2, 29), "Mañana, 29/02"),
        (date(2028, 2, 29), date(2028, 3, 1), "Mañana, 01/03"),
        (date(2027, 2, 28), date(2027, 3, 1), "Mañana, 01/03"),
    ],
    ids=["fin_de_anio", "vispera_de_bisiesto", "despues_de_bisiesto", "febrero_comun"],
)
def test_el_aviso_previo_funciona_al_cambiar_de_mes_y_de_anio(
    avisos, monkeypatch, hoy_falso, dia_evento, texto
):
    repository.guardar(Evento("x", dia_evento))

    fijar_hoy(monkeypatch, hoy_falso)
    scheduler.revisar_avisos()

    assert avisos == [("x", texto)]


def test_un_evento_reprogramado_vuelve_a_avisar(avisos, guardar_evento, hoy):
    from backend import service

    evento = guardar_evento("Dentista", dias=1)
    scheduler.revisar_avisos()  # aviso previo de la fecha original
    assert len(avisos) == 1

    # Al cambiar la fecha, el service resetea los avisos...
    evento = repository.buscar_por_id(evento.id)
    evento.fecha = hoy
    service.actualizar_evento(evento)

    scheduler.revisar_avisos()  # ...y entonces corresponde el aviso del nuevo día
    assert avisos[-1] == ("Dentista", f"Hoy, {hoy.strftime('%d/%m')}")
    assert len(avisos) == 2


# --- cuando la notificación falla (punto 2 pedido) -----------------------------
def test_si_la_notificacion_falla_el_aviso_queda_pendiente(monkeypatch, guardar_evento):
    evento = guardar_evento(dias=0)

    def falla(titulo, mensaje):
        raise RuntimeError("no hay sistema de notificaciones")

    monkeypatch.setattr(scheduler, "notificar", falla)

    scheduler.revisar_avisos()  # no tiene que lanzar el error

    assert repository.buscar_por_id(evento.id).aviso_dia_enviado is False


def test_un_aviso_que_fallo_se_reintenta_en_la_siguiente_revision(
    monkeypatch, guardar_evento
):
    evento = guardar_evento("Parcial", dias=0)
    intentos = []

    def falla_la_primera_vez(titulo, mensaje):
        intentos.append(titulo)
        if len(intentos) == 1:
            raise RuntimeError("falló")

    monkeypatch.setattr(scheduler, "notificar", falla_la_primera_vez)

    scheduler.revisar_avisos()
    scheduler.revisar_avisos()
    scheduler.revisar_avisos()

    assert intentos == ["Parcial", "Parcial"]  # falló, reintentó y no repitió más
    assert repository.buscar_por_id(evento.id).aviso_dia_enviado is True


def test_un_aviso_que_falla_no_frena_a_los_demas(monkeypatch, guardar_evento):
    malo = guardar_evento("malo", dias=0)
    bueno_1 = guardar_evento("bueno 1", dias=0)
    bueno_2 = guardar_evento("bueno 2", dias=1)
    enviados = []

    def falla_con_uno(titulo, mensaje):
        if titulo == "malo":
            raise RuntimeError("falló")
        enviados.append(titulo)

    monkeypatch.setattr(scheduler, "notificar", falla_con_uno)

    scheduler.revisar_avisos()

    assert sorted(enviados) == ["bueno 1", "bueno 2"]
    assert repository.buscar_por_id(malo.id).aviso_dia_enviado is False
    assert repository.buscar_por_id(bueno_1.id).aviso_dia_enviado is True
    assert repository.buscar_por_id(bueno_2.id).aviso_previo_enviado is True


def test_el_error_de_una_notificacion_queda_anotado(
    monkeypatch, guardar_evento, caplog
):
    guardar_evento(dias=0)

    def falla(titulo, mensaje):
        raise RuntimeError("detalle del problema")

    monkeypatch.setattr(scheduler, "notificar", falla)

    scheduler.revisar_avisos()

    assert "No se pudo mostrar el aviso" in caplog.text
    assert "detalle del problema" in caplog.text


# --- iniciar ------------------------------------------------------------------
def test_iniciar_revisa_al_arrancar_y_programa_la_repeticion(avisos, guardar_evento):
    guardar_evento("hoy", dias=0)

    planificador = scheduler.iniciar()
    try:
        assert [titulo for titulo, _ in avisos] == ["hoy"]  # revisión inmediata
        assert planificador.running
        tareas = planificador.get_jobs()
        assert len(tareas) == 1
        assert tareas[0].trigger.interval == timedelta(minutes=5)
    finally:
        planificador.shutdown(wait=False)


def test_iniciar_no_falla_si_la_revision_inicial_falla(monkeypatch):
    def falla():
        raise RuntimeError("la base no responde")

    monkeypatch.setattr(scheduler, "revisar_avisos", falla)

    planificador = scheduler.iniciar()  # la aplicación tiene que poder abrir igual
    try:
        assert planificador.running
    finally:
        planificador.shutdown(wait=False)


def test_iniciar_no_falla_si_las_notificaciones_no_funcionan(
    monkeypatch, guardar_evento
):
    guardar_evento(dias=0)

    def falla(titulo, mensaje):
        raise NotImplementedError("sin notificaciones en este sistema")

    monkeypatch.setattr(scheduler, "notificar", falla)

    planificador = scheduler.iniciar()
    try:
        assert planificador.running
    finally:
        planificador.shutdown(wait=False)
