from datetime import date, time


class Evento:
    id: int | None
    nombre: str
    fecha: date
    hora: time | None
    descripcion: str | None
    aviso_previo_enviado: bool
    aviso_dia_enviado: bool

    def __init__(
        self,
        nombre,
        fecha,
        id=None,
        hora=None,
        descripcion=None,
        aviso_previo_enviado=False,
        aviso_dia_enviado=False,
    ):
        """
        Constructor de la clase evento, cuenta con ciertos atributos por defecto.
        """
        self.id = id
        self.nombre = nombre
        self.fecha = fecha
        self.hora = hora
        self.descripcion = descripcion
        self.aviso_previo_enviado = aviso_previo_enviado
        self.aviso_dia_enviado = aviso_dia_enviado
