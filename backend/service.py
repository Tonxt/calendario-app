import calendar
from datetime import date, datetime, time

from backend.models import Evento
from backend.repository import (
    guardar,
    actualizar,
    buscar_por_id,
    eliminar,
    buscar_por_fecha,
    buscar_entre_fechas,
)

NOMBRE_MAXIMO = 100  # cantidad máxima de letras del nombre de un evento


class ErrorValidacion(Exception):
    """Se lanza cuando un evento incumple reglas"""


def _es_fecha(valor) -> bool:
    # datetime (fecha y hora juntas) es una subclase de date, así que
    # isinstance(valor, date) también lo acepta. Hay que descartarlo aparte:
    # no se puede comparar con date.today() ni guardar como una fecha sola.
    return isinstance(valor, date) and not isinstance(valor, datetime)


def _validar_evento(evento, exigir_fecha_futura=True):
    if not isinstance(evento, Evento):
        raise ErrorValidacion("Debe indicar un evento")
    if not isinstance(evento.nombre, str):
        raise ErrorValidacion("Debe ingresar un nombre valido")
    evento.nombre = evento.nombre.strip()
    if not evento.nombre:
        raise ErrorValidacion("El nombre del evento no puede estar vacio")
    if len(evento.nombre) > NOMBRE_MAXIMO:
        raise ErrorValidacion(
            f"El nombre no puede tener mas de {NOMBRE_MAXIMO} caracteres"
        )
    if not _es_fecha(evento.fecha):
        raise ErrorValidacion("Debe indicar una fecha valida")
    if exigir_fecha_futura and evento.fecha < date.today():
        raise ErrorValidacion("La fecha del evento no puede estar en el pasado")
    if not isinstance(evento.hora, time | None):
        raise ErrorValidacion("Debe indicar un horario valido")
    if not isinstance(evento.descripcion, str | None):
        raise ErrorValidacion("La descripcion debe ser un texto")
    if evento.descripcion is not None:
        # Una descripción vacía o solo con espacios es lo mismo que no tener.
        evento.descripcion = evento.descripcion.strip() or None
    if not isinstance(evento.aviso_previo_enviado, bool) or not isinstance(
        evento.aviso_dia_enviado, bool
    ):
        raise ErrorValidacion("El estado de los avisos no es valido")


def crear_evento(evento):
    if isinstance(evento, Evento) and evento.id is not None:
        # Guardarlo de nuevo crearía un duplicado en la base.
        raise ErrorValidacion("El evento ya fue guardado")
    _validar_evento(evento)
    # Un evento nuevo todavía no pudo haber enviado ningún aviso.
    evento.aviso_previo_enviado = False
    evento.aviso_dia_enviado = False
    return guardar(evento)


def actualizar_evento(evento):
    if not isinstance(evento, Evento):
        raise ErrorValidacion("Debe indicar un evento")
    original = buscar_por_id(evento.id)
    if original is None:
        raise ErrorValidacion("El evento no existe")
    # La regla de "no en el pasado" solo se aplica si la fecha cambió. Así se
    # puede corregir el nombre o la descripción de un evento que ya pasó.
    cambio_la_fecha = evento.fecha != original.fecha
    _validar_evento(evento, exigir_fecha_futura=cambio_la_fecha)
    if cambio_la_fecha:
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
    if not _es_fecha(fecha):
        raise ErrorValidacion("Debe indicar una fecha valida")
    return buscar_por_fecha(fecha)


def eventos_del_mes(anio, mes):
    # bool también cuenta como int en Python (True vale 1), por eso se descarta.
    son_enteros = all(
        isinstance(valor, int) and not isinstance(valor, bool) for valor in (anio, mes)
    )
    if (
        not son_enteros
        or not 1 <= mes <= 12
        or not date.min.year <= anio <= date.max.year
    ):
        raise ErrorValidacion("Debe indicar un mes valido")
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return buscar_entre_fechas(date(anio, mes, 1), date(anio, mes, ultimo_dia))
