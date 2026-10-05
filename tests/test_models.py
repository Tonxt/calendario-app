"""Pruebas de la clase Evento."""

from datetime import date, time

from backend.models import Evento


def test_evento_minimo_usa_los_valores_por_defecto():
    evento = Evento("Dentista", date(2030, 1, 15))

    assert evento.nombre == "Dentista"
    assert evento.fecha == date(2030, 1, 15)
    assert evento.id is None
    assert evento.hora is None
    assert evento.descripcion is None
    assert evento.aviso_previo_enviado is False
    assert evento.aviso_dia_enviado is False


def test_evento_completo_guarda_todos_los_datos():
    evento = Evento(
        "Parcial",
        date(2030, 6, 1),
        id=7,
        hora=time(18, 30),
        descripcion="Aula 305",
        aviso_previo_enviado=True,
        aviso_dia_enviado=True,
    )

    assert vars(evento) == {
        "id": 7,
        "nombre": "Parcial",
        "fecha": date(2030, 6, 1),
        "hora": time(18, 30),
        "descripcion": "Aula 305",
        "aviso_previo_enviado": True,
        "aviso_dia_enviado": True,
    }


def test_cada_evento_tiene_sus_propios_datos():
    # Si los atributos fueran de clase (compartidos), cambiar uno cambiaría el otro.
    uno = Evento("Uno", date(2030, 1, 1))
    otro = Evento("Otro", date(2030, 1, 2))

    uno.nombre = "Cambiado"
    uno.aviso_dia_enviado = True

    assert otro.nombre == "Otro"
    assert otro.aviso_dia_enviado is False
