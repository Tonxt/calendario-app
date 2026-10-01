from datetime import date, time
from backend.repository import (
    guardar,
    actualizar,
    buscar_por_id,
    eliminar,
    buscar_por_fecha,
    buscar_entre_fechas,
)
import calendar


class ErrorValidacion(Exception):
    """Se lanza cuando un evento incumple reglas"""


def _validar_evento(evento):
    if not isinstance(evento.nombre, str):
        raise ErrorValidacion("Debe ingresar un nombre valido")
    evento.nombre = evento.nombre.strip()
    if not evento.nombre:
        raise ErrorValidacion("El nombre del evento no puede estar vacio")
    if not isinstance(evento.fecha, date):
        raise ErrorValidacion("Debe indicar una fecha valida")
    if evento.fecha < date.today():
        raise ErrorValidacion("La fecha del evento no puede estar en el pasado")
    if not isinstance(evento.hora, time | None):
        raise ErrorValidacion("Debe indicar un horario valido")


def crear_evento(evento):
    _validar_evento(evento)
    return guardar(evento)


def actualizar_evento(evento):
    original = buscar_por_id(evento.id)
    if original is None:
        raise ErrorValidacion("El evento no existe")
    _validar_evento(evento)
    if evento.fecha != original.fecha:
        evento.aviso_previo_enviado = False
        evento.aviso_dia_enviado = False
    actualizar(evento)


def obtener_evento(id):
    evento = buscar_por_id(id)
    if evento is None:
        raise ErrorValidacion("El evento no existe")
    else:
        return evento


def eliminar_evento(id):
    obtener_evento(id)
    eliminar(id)


def eventos_del_dia(fecha):
    return buscar_por_fecha(fecha)


def eventos_del_mes(anio, mes):
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return buscar_entre_fechas(date(anio, mes, 1), date(anio, mes, ultimo_dia))
