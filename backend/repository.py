from backend.database import obtener_conexion
from datetime import time, date
from backend.models import Evento


def _hora_a_texto(hora: time | None) -> str | None:
    return None if hora is None else hora.isoformat(timespec="minutes")


def _texto_a_hora(hora: str | None) -> time | None:
    return None if hora is None else time.fromisoformat(hora)


def _fila_a_evento(fila) -> Evento:
    fecha = date.fromisoformat(fila[2])
    hora = _texto_a_hora(fila[3])
    aviso_previo_enviado = bool(fila[5])
    aviso_dia_enviado = bool(fila[6])
    evento = Evento(
        nombre=fila[1],
        fecha=fecha,
        id=fila[0],
        hora=hora,
        descripcion=fila[4],
        aviso_previo_enviado=aviso_previo_enviado,
        aviso_dia_enviado=aviso_dia_enviado,
    )
    return evento


def guardar(evento):
    con = obtener_conexion()
    insercion = con.execute(
        "INSERT INTO eventos (nombre,fecha,hora,descripcion) VALUES (?,?,?,?)",
        (
            evento.nombre,
            evento.fecha.isoformat(),
            _hora_a_texto(evento.hora),
            evento.descripcion,
        ),
    )
    evento.id = insercion.lastrowid
    con.commit()
    con.close()
    return evento


def buscar_por_id(id):
    con = obtener_conexion()
    consulta = con.execute(
        "SELECT id,nombre,fecha,hora,descripcion,aviso_previo_enviado,aviso_dia_enviado FROM eventos WHERE id=?",
        (id,),
    )
    fila = consulta.fetchone()
    con.close()
    return None if fila is None else _fila_a_evento(fila)
