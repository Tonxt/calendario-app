from backend.database import obtener_conexion
from datetime import time, date
from backend.models import Evento

COLUMNAS_EVENTO = (
    "id, nombre, fecha, hora, descripcion, aviso_previo_enviado, aviso_dia_enviado"
)

SQL_INSERTAR_EVENTO = (
    "INSERT INTO eventos (nombre, fecha, hora, descripcion) VALUES (?, ?, ?, ?)"
)

SQL_BUSCAR_POR_ID = f"SELECT {COLUMNAS_EVENTO} FROM eventos WHERE id = ?"

SQL_BUSCAR_POR_FECHA = (
    f"SELECT {COLUMNAS_EVENTO} FROM eventos WHERE fecha = ? ORDER BY hora"
)

SQL_BUSCAR_ENTRE_FECHAS = f"SELECT {COLUMNAS_EVENTO} FROM eventos WHERE fecha BETWEEN ? AND ? ORDER BY fecha, hora"

SQL_ACTUALIZAR_EVENTO = "UPDATE eventos SET nombre=?,fecha=?,hora=?,descripcion=?,aviso_previo_enviado=?,aviso_dia_enviado=? WHERE id = ?"

SQL_ELIMINAR_EVENTO = "DELETE FROM eventos WHERE id = ?"

SQL_BUSCAR_AVISOS_PREVIOS_PENDIENTES = f"SELECT {COLUMNAS_EVENTO} FROM eventos WHERE fecha = ? AND aviso_previo_enviado = 0"

SQL_BUSCAR_AVISOS_DIA_PENDIENTES = (
    f"SELECT {COLUMNAS_EVENTO} FROM eventos WHERE fecha = ? AND aviso_dia_enviado = 0"
)

SQL_MARCAR_AVISO_PREVIO_ENVIADO = (
    "UPDATE eventos SET aviso_previo_enviado=1 WHERE id = ?"
)

SQL_MARCAR_AVISO_DIA_ENVIADO = "UPDATE eventos SET aviso_dia_enviado=1 WHERE id = ?"


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
        SQL_INSERTAR_EVENTO,
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
        SQL_BUSCAR_POR_ID,
        (id,),
    )
    fila = consulta.fetchone()
    con.close()
    return None if fila is None else _fila_a_evento(fila)


def buscar_por_fecha(fecha):
    con = obtener_conexion()
    consulta = con.execute(
        SQL_BUSCAR_POR_FECHA,
        (fecha.isoformat(),),
    )
    lista = consulta.fetchall()
    con.close()
    eventos = [_fila_a_evento(fila) for fila in lista]
    return eventos


def buscar_entre_fechas(desde, hasta):
    con = obtener_conexion()
    consulta = con.execute(
        SQL_BUSCAR_ENTRE_FECHAS, (desde.isoformat(), hasta.isoformat())
    )
    lista = consulta.fetchall()
    con.close()
    eventos = [_fila_a_evento(fila) for fila in lista]
    return eventos


def actualizar(evento):
    con = obtener_conexion()
    con.execute(
        SQL_ACTUALIZAR_EVENTO,
        (
            evento.nombre,
            evento.fecha.isoformat(),
            _hora_a_texto(evento.hora),
            evento.descripcion,
            evento.aviso_previo_enviado,
            evento.aviso_dia_enviado,
            evento.id,
        ),
    )
    con.commit()
    con.close()


def eliminar(id):
    con = obtener_conexion()
    con.execute(SQL_ELIMINAR_EVENTO, (id,))
    con.commit()
    con.close()


def buscar_avisos_previos_pendientes(fecha):
    con = obtener_conexion()
    consulta = con.execute(
        SQL_BUSCAR_AVISOS_PREVIOS_PENDIENTES,
        (fecha.isoformat(),),
    )
    lista = consulta.fetchall()
    con.close()
    eventos = [_fila_a_evento(fila) for fila in lista]
    return eventos


def buscar_avisos_dia_pendientes(fecha):
    con = obtener_conexion()
    consulta = con.execute(
        SQL_BUSCAR_AVISOS_DIA_PENDIENTES,
        (fecha.isoformat(),),
    )
    lista = consulta.fetchall()
    con.close()
    eventos = [_fila_a_evento(fila) for fila in lista]
    return eventos


def marcar_aviso_previo_enviado(id):
    con = obtener_conexion()
    con.execute(SQL_MARCAR_AVISO_PREVIO_ENVIADO, (id,))
    con.commit()
    con.close()


def marcar_aviso_dia_enviado(id):
    con = obtener_conexion()
    con.execute(SQL_MARCAR_AVISO_DIA_ENVIADO, (id,))
    con.commit()
    con.close()
