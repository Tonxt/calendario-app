from backend.database import obtener_conexion
from datetime import time


def _hora_a_texto(hora: time | None) -> str | None:
    return None if hora is None else hora.isoformat(timespec="minutes")


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
