"""Conversión entre los datos del backend y los textos que ve el usuario.

El backend trabaja con objetos `date` y `time`. La interfaz muestra y recibe
textos ("20/10/2026", "10:30"). Este módulo hace ese pasaje en los dos
sentidos, así las pantallas no repiten esa lógica.
"""

from datetime import date, datetime, time

MESES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)

DIAS_CORTOS = ("LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM")
DIAS_LARGOS = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)

FORMATOS_FECHA = ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y")
FORMATOS_HORA = ("%H:%M", "%H.%M", "%H")


def titulo_mes(anio: int, mes: int) -> str:
    """'Octubre 2026'"""
    return f"{MESES[mes - 1]} {anio}"


def fecha_larga(fecha: date) -> str:
    """'Martes 20 de octubre de 2026'"""
    dia_semana = DIAS_LARGOS[fecha.weekday()]
    mes = MESES[fecha.month - 1].lower()
    return f"{dia_semana} {fecha.day} de {mes} de {fecha.year}"


def fecha_a_texto(fecha: date) -> str:
    """'20/10/2026'"""
    return fecha.strftime("%d/%m/%Y")


def hora_a_texto(hora: time | None) -> str:
    """'10:30', o un texto vacío si el evento no tiene hora."""
    return "" if hora is None else hora.strftime("%H:%M")


def texto_a_fecha(texto: str) -> date:
    """Convierte lo que escribió el usuario en un `date`.

    Lanza ValueError, con un mensaje para mostrarle, si no se entiende.
    """
    texto = texto.strip()
    for formato in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError("Escribí la fecha como dd/mm/aaaa, por ejemplo 20/10/2026")


def texto_a_hora(texto: str) -> time | None:
    """Convierte lo que escribió el usuario en un `time`.

    Un texto vacío significa "sin hora" y devuelve None.
    Lanza ValueError, con un mensaje para mostrarle, si no se entiende.
    """
    texto = texto.strip()
    if not texto:
        return None
    for formato in FORMATOS_HORA:
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    raise ValueError("Escribí la hora como hh:mm, por ejemplo 18:30, o dejala vacía")


def resumen_evento(evento) -> str:
    """'10:30 Dentista', o solo 'Dentista' si no tiene hora."""
    if evento.hora is None:
        return evento.nombre
    return f"{hora_a_texto(evento.hora)} {evento.nombre}"


def recortar(texto: str, maximo: int) -> str:
    """Corta el texto y agrega puntos suspensivos si no entra en `maximo` letras."""
    if len(texto) <= maximo:
        return texto
    if maximo <= 0:
        return ""
    return texto[: maximo - 1].rstrip() + "…"
