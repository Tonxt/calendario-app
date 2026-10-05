"""Pruebas de punta a punta: varias capas trabajando juntas, como en el uso real."""

import threading
from datetime import time, timedelta

from backend import repository, scheduler, service
from backend.models import Evento
from backend.service import ErrorValidacion
from tests.conftest import contar_eventos


def test_la_vida_completa_de_un_evento(monkeypatch, hoy, manana):
    avisos = []
    monkeypatch.setattr(
        scheduler, "notificar", lambda titulo, mensaje: avisos.append((titulo, mensaje))
    )

    # 1. El usuario crea un evento para mañana.
    evento = service.crear_evento(
        Evento("Dentista", manana, hora=time(10, 30), descripcion="Control")
    )
    assert [e.id for e in service.eventos_del_dia(manana)] == [evento.id]
    assert evento.id in [
        e.id for e in service.eventos_del_mes(manana.year, manana.month)
    ]

    # 2. El scheduler le avisa una sola vez.
    scheduler.revisar_avisos()
    scheduler.revisar_avisos()
    assert avisos == [("Dentista", f"Mañana, {manana.strftime('%d/%m')}")]

    # 3. Corrige el nombre: el aviso ya enviado no se repite.
    evento = service.obtener_evento(evento.id)
    evento.nombre = "Odontólogo"
    service.actualizar_evento(evento)
    scheduler.revisar_avisos()
    assert len(avisos) == 1

    # 4. Lo adelanta para hoy: corresponde un aviso nuevo, con el nombre corregido.
    evento = service.obtener_evento(evento.id)
    evento.fecha = hoy
    service.actualizar_evento(evento)
    scheduler.revisar_avisos()
    assert avisos[-1] == ("Odontólogo", f"Hoy, {hoy.strftime('%d/%m')}")
    assert len(avisos) == 2

    # 5. Lo elimina: desaparece de todas las consultas y no avisa más.
    service.eliminar_evento(evento.id)
    assert service.eventos_del_dia(hoy) == []
    scheduler.revisar_avisos()
    assert len(avisos) == 2
    assert contar_eventos() == 0


def test_un_intento_invalido_en_el_medio_no_rompe_nada(manana):
    bueno = service.crear_evento(Evento("Bueno", manana))

    for malo in [
        Evento("", manana),
        Evento("x", "mañana"),
        Evento("x", manana, hora="10"),
    ]:
        try:
            service.crear_evento(malo)
        except ErrorValidacion:
            pass

    assert contar_eventos() == 1
    assert service.obtener_evento(bueno.id).nombre == "Bueno"


def test_los_datos_sobreviven_a_cerrar_y_volver_a_abrir(manana):
    # Cada función abre y cierra su propia conexión: lo guardado tiene que
    # estar en el archivo, no en la memoria del programa.
    evento = service.crear_evento(Evento("Persistente", manana, hora=time(8, 0)))

    from backend import database

    database.crear_tablas()  # lo que hace main.py en cada arranque

    assert vars(service.obtener_evento(evento.id)) == vars(evento)


def test_el_scheduler_y_la_interfaz_pueden_usar_la_base_a_la_vez(monkeypatch, hoy):
    # En la aplicación real, el scheduler corre en otro hilo mientras el
    # usuario crea eventos. Acá se fuerza esa situación muchas veces seguidas.
    monkeypatch.setattr(scheduler, "notificar", lambda titulo, mensaje: None)
    errores = []

    def crear_muchos(prefijo):
        try:
            for numero in range(40):
                service.crear_evento(Evento(f"{prefijo} {numero}", hoy))
        except Exception as error:  # cualquier error hace fallar la prueba
            errores.append(error)

    def revisar_muchas_veces():
        try:
            for _ in range(40):
                scheduler.revisar_avisos()
        except Exception as error:
            errores.append(error)

    hilos = [
        threading.Thread(target=crear_muchos, args=("a",)),
        threading.Thread(target=crear_muchos, args=("b",)),
        threading.Thread(target=revisar_muchas_veces),
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=60)

    assert errores == []
    assert contar_eventos() == 80
    scheduler.revisar_avisos()  # una última pasada para los que quedaron pendientes
    assert repository.buscar_avisos_dia_pendientes(hoy) == []


def test_un_mes_cargado_se_consulta_completo_y_ordenado(hoy):
    primer_dia = (hoy.replace(day=1) + timedelta(days=62)).replace(
        day=1
    )  # dentro de 2 meses
    for dia in range(28):
        for hora in (time(18, 0), None, time(9, 0)):
            service.crear_evento(
                Evento("x", primer_dia + timedelta(days=dia), hora=hora)
            )

    eventos = service.eventos_del_mes(primer_dia.year, primer_dia.month)

    assert len(eventos) == 84
    claves = [(e.fecha, e.hora is not None, e.hora) for e in eventos]
    assert claves == sorted(claves)  # por fecha, y sin hora primero
