"""Pruebas de la interfaz gráfica.

Abren la ventana de verdad (se ve parpadear unos segundos) y simulan lo que
haría el usuario llamando a los mismos métodos que disparan los botones. Si la
máquina no tiene pantalla (por ejemplo, un servidor), se saltean solas.
"""

import threading
import time as reloj
import tkinter
from datetime import date, time, timedelta

import pytest

from backend import repository, service
from backend.models import Evento
from interfaz import app as modulo_app
from interfaz import bandeja as modulo_bandeja
from interfaz import estilos
from interfaz.app import App
from interfaz.dialogos import DetalleEvento, EventosDelDia
from interfaz.formato import fecha_a_texto
from interfaz.formulario_evento import FormularioEvento
from tests.conftest import contar_eventos


def esperar(app, milisegundos=250):
    """Deja que la ventana procese sus tareas pendientes durante un rato."""
    fin = reloj.time() + milisegundos / 1000
    while reloj.time() < fin:
        app.update()
        reloj.sleep(0.01)


@pytest.fixture
def app():
    # Las fuentes quedan guardadas para reutilizarlas, pero pertenecen a la
    # ventana que las creó: cada prueba abre una ventana nueva y necesita las suyas.
    estilos.fuente.cache_clear()
    try:
        ventana = App()
    except tkinter.TclError as error:
        pytest.skip(f"No hay pantalla para abrir la ventana: {error}")
    ventana.geometry("1100x700+0+0")
    esperar(ventana, 300)
    yield ventana
    try:
        ventana.destroy()
    except tkinter.TclError:
        pass  # la prueba ya la había cerrado


def ventana_abierta(app, clase):
    """La ventana emergente de ese tipo que está abierta, o None."""
    abiertas = [w for w in app.winfo_children() if isinstance(w, clase)]
    return abiertas[-1] if abiertas else None


def chips_de(app, fecha):
    """Los textos de los eventos dibujados en la celda de esa fecha."""
    for fila in app.grilla._celdas:
        for celda in fila:
            if celda.fecha == fecha and celda.winfo_ismapped():
                return [chip.cget("text") for chip in celda._chips]
    return None


def escribir(campo, texto):
    campo.delete(0, "end")
    campo.insert(0, texto)


# --- arranque y navegación ----------------------------------------------------
def test_abre_en_el_mes_actual(app, hoy):
    assert (app.anio, app.mes) == (hoy.year, hoy.month)
    assert str(hoy.year) in app.titulo_mes.cget("text")


def test_abre_con_la_base_vacia_sin_errores(app, hoy):
    assert chips_de(app, hoy) == []


def test_avanzar_doce_meses_vuelve_al_mismo_mes_del_anio_siguiente(app, hoy):
    for _ in range(12):
        app.mes_siguiente()

    assert (app.anio, app.mes) == (hoy.year + 1, hoy.month)


def test_retroceder_doce_meses_vuelve_al_mismo_mes_del_anio_anterior(app, hoy):
    for _ in range(12):
        app.mes_anterior()

    assert (app.anio, app.mes) == (hoy.year - 1, hoy.month)


def test_de_diciembre_pasa_a_enero_del_anio_siguiente(app):
    app.ir_a_fecha(date(2030, 12, 15))

    app.mes_siguiente()

    assert (app.anio, app.mes) == (2031, 1)
    assert app.titulo_mes.cget("text") == "Enero 2031"


def test_de_enero_pasa_a_diciembre_del_anio_anterior(app):
    app.ir_a_fecha(date(2030, 1, 15))

    app.mes_anterior()

    assert (app.anio, app.mes) == (2029, 12)
    assert app.titulo_mes.cget("text") == "Diciembre 2029"


def test_hoy_vuelve_al_mes_actual(app, hoy):
    app.ir_a_fecha(date(2035, 7, 1))

    app.ir_a_hoy()

    assert (app.anio, app.mes) == (hoy.year, hoy.month)


@pytest.mark.parametrize(
    "anio, mes, semanas",
    [(2027, 2, 4), (2026, 10, 5), (2026, 8, 6)],
    ids=["mes_de_4_semanas", "mes_de_5_semanas", "mes_de_6_semanas"],
)
def test_la_grilla_muestra_las_semanas_justas(app, anio, mes, semanas):
    app.ir_a_fecha(date(anio, mes, 1))
    esperar(app, 100)

    filas_visibles = [fila for fila in app.grilla._celdas if fila[0].winfo_ismapped()]
    assert len(filas_visibles) == semanas


def test_cada_fecha_del_mes_aparece_una_sola_vez(app):
    app.ir_a_fecha(date(2028, 2, 1))  # febrero bisiesto
    esperar(app, 100)

    fechas = [
        celda.fecha
        for fila in app.grilla._celdas
        for celda in fila
        if celda.winfo_ismapped() and celda.fecha.month == 2
    ]
    assert fechas == [date(2028, 2, dia) for dia in range(1, 30)]


def test_navegar_muy_rapido_no_rompe_nada(app):
    for _ in range(40):
        app.mes_siguiente()
    for _ in range(80):
        app.mes_anterior()
    esperar(app, 200)

    assert app.titulo_mes.cget("text")  # sigue viva y con título


# --- los eventos en la grilla ---------------------------------------------------
def test_los_eventos_guardados_se_ven_en_su_dia(app, guardar_evento, hoy):
    guardar_evento("Dentista", dias=0, hora=time(10, 30))
    guardar_evento("Cumpleaños", dias=0)

    app.actualizar_vista()

    assert chips_de(app, hoy) == ["Cumpleaños", "10:30 Dentista"]


def test_muchos_eventos_en_un_dia_muestran_mas_n(app, guardar_evento, hoy):
    for numero in range(30):
        guardar_evento(f"evento {numero}", dias=0)

    app.actualizar_vista()
    esperar(app, 200)

    chips = chips_de(app, hoy)
    assert chips[-1].startswith("+") and chips[-1].endswith("más")
    ocultos = int(chips[-1].split()[0])
    assert (len(chips) - 1) + ocultos == 30  # visibles + ocultos = todos


def test_un_nombre_larguisimo_se_recorta_en_la_grilla(app, hoy):
    repository.guardar(Evento("a" * 5000, hoy))

    app.actualizar_vista()
    esperar(app, 200)

    (chip,) = chips_de(app, hoy)
    assert len(chip) < 60 and chip.endswith("…")


@pytest.mark.parametrize(
    "nombre", ["日本語 🎉🎂", "línea 1\nlínea 2", "{llaves} %s %d \\n", "<b>html</b>"]
)
def test_nombres_raros_no_rompen_el_dibujo(app, hoy, nombre):
    repository.guardar(Evento(nombre, hoy))

    app.actualizar_vista()
    esperar(app, 150)

    assert len(chips_de(app, hoy)) == 1


def test_se_ven_los_eventos_de_los_dias_del_mes_vecino(app):
    # La grilla de octubre de 2026 empieza el lunes 28 de septiembre.
    repository.guardar(Evento("Viaje", date(2026, 9, 29)))

    app.ir_a_fecha(date(2026, 10, 1))
    esperar(app, 100)

    assert chips_de(app, date(2026, 9, 29)) == ["Viaje"]


@pytest.mark.parametrize("tamano", ["820x560", "1600x1000", "820x1000", "1600x560"])
def test_cambiar_el_tamano_de_la_ventana_no_pierde_eventos(
    app, guardar_evento, hoy, tamano
):
    for numero in range(6):
        guardar_evento(f"evento {numero}", dias=0)
    app.actualizar_vista()

    app.geometry(f"{tamano}+0+0")
    esperar(app, 500)

    chips = chips_de(app, hoy)
    ocultos = int(chips[-1].split()[0]) if chips[-1].startswith("+") else 0
    visibles = len(chips) - (1 if ocultos else 0)
    assert visibles + ocultos == 6


def test_la_lista_de_hoy_muestra_solo_los_eventos_de_hoy(app, guardar_evento):
    guardar_evento("de hoy", dias=0)
    guardar_evento("de mañana", dias=1)

    app.actualizar_vista()

    textos = [w.cget("text") for w in app.barra_lateral._lista_hoy.winfo_children()]
    assert textos == ["de hoy"]


def test_el_mini_calendario_puede_ir_y_volver_muchos_anios(app):
    mini = app.barra_lateral.mini_calendario
    for _ in range(30):
        mini._mes_anterior()
    for _ in range(60):
        mini._mes_siguiente()

    assert mini._titulo.cget("text")


# --- crear ---------------------------------------------------------------------
def test_crear_un_evento_desde_el_formulario(app, manana):
    app.nuevo_evento(manana)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    assert formulario._fecha.get() == fecha_a_texto(manana)  # fecha ya cargada

    escribir(formulario._nombre, "Parcial")
    escribir(formulario._hora, "18:30")
    formulario._descripcion.insert("1.0", "Aula 305")
    formulario._guardar()
    esperar(app)

    assert ventana_abierta(app, FormularioEvento) is None  # se cerró
    (evento,) = service.eventos_del_dia(manana)
    assert (evento.nombre, evento.hora, evento.descripcion) == (
        "Parcial",
        time(18, 30),
        "Aula 305",
    )
    if manana.month == app.mes:
        assert chips_de(app, manana) == ["18:30 Parcial"]  # y ya se ve en la grilla


def test_el_boton_crear_propone_la_fecha_de_hoy(app, hoy):
    app.nuevo_evento()
    esperar(app)

    assert ventana_abierta(app, FormularioEvento)._fecha.get() == fecha_a_texto(hoy)


@pytest.mark.parametrize(
    "nombre, fecha, hora, parte_del_error",
    [
        ("", None, "", "nombre"),
        ("   ", None, "", "nombre"),
        ("a" * 101, None, "", "100"),
        ("x", "31/02/2030", "", "dd/mm/aaaa"),
        ("x", "", "", "dd/mm/aaaa"),
        ("x", "hola", "", "dd/mm/aaaa"),
        ("x", "2030-01-01", "", "dd/mm/aaaa"),
        ("x", "01/01/2020", "", "pasado"),
        ("x", None, "25:00", "hh:mm"),
        ("x", None, "seis", "hh:mm"),
    ],
    ids=[
        "sin_nombre",
        "nombre_solo_espacios",
        "nombre_muy_largo",
        "fecha_inexistente",
        "fecha_vacia",
        "fecha_con_letras",
        "fecha_en_otro_formato",
        "fecha_pasada",
        "hora_inexistente",
        "hora_con_letras",
    ],
)
def test_el_formulario_muestra_el_error_y_no_guarda(
    app, manana, nombre, fecha, hora, parte_del_error
):
    app.nuevo_evento(manana)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    escribir(formulario._nombre, nombre)
    if fecha is not None:
        escribir(formulario._fecha, fecha)
    escribir(formulario._hora, hora)

    formulario._guardar()
    esperar(app, 100)

    assert parte_del_error in formulario._error.cget("text")
    assert formulario.winfo_exists()  # sigue abierto para corregir
    assert contar_eventos() == 0


def test_despues_de_un_error_se_puede_corregir_y_guardar(app, manana):
    app.nuevo_evento(manana)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)

    formulario._guardar()  # sin nombre
    assert formulario._error.cget("text")

    escribir(formulario._nombre, "Ahora sí")
    formulario._guardar()
    esperar(app)

    assert contar_eventos() == 1


def test_cancelar_el_formulario_no_guarda(app, manana):
    app.nuevo_evento(manana)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    escribir(formulario._nombre, "No guardar")

    formulario.destroy()
    esperar(app, 100)

    assert contar_eventos() == 0


def test_guardar_dos_veces_seguidas_no_duplica(app, manana):
    # Doble clic nervioso en "Guardar".
    app.nuevo_evento(manana)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    escribir(formulario._nombre, "Una sola vez")

    formulario._guardar()
    try:
        formulario._guardar()
    except Exception:
        pass  # la ventana ya se había cerrado: lo importante es que no duplique
    esperar(app)

    assert contar_eventos() == 1


# --- editar --------------------------------------------------------------------
def test_editar_muestra_los_datos_actuales_y_guarda_los_cambios(app, manana):
    evento = service.crear_evento(
        Evento("Dentista", manana, hora=time(10, 30), descripcion="Control")
    )
    app.editar_evento(evento)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)

    assert formulario._nombre.get() == "Dentista"
    assert formulario._fecha.get() == fecha_a_texto(manana)
    assert formulario._hora.get() == "10:30"
    assert formulario._descripcion.get("1.0", "end-1c") == "Control"

    escribir(formulario._nombre, "Odontólogo")
    escribir(formulario._hora, "")  # le saca la hora
    formulario._descripcion.delete("1.0", "end")
    formulario._guardar()
    esperar(app)

    guardado = service.obtener_evento(evento.id)
    assert (guardado.nombre, guardado.hora, guardado.descripcion) == (
        "Odontólogo",
        None,
        None,
    )
    assert contar_eventos() == 1  # editó, no creó otro


def test_editar_con_un_error_no_cambia_el_evento(app, manana):
    evento = service.crear_evento(Evento("Original", manana))
    app.editar_evento(evento)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    escribir(formulario._nombre, "")

    formulario._guardar()

    assert formulario._error.cget("text")
    assert service.obtener_evento(evento.id).nombre == "Original"
    assert evento.nombre == "Original"  # tampoco tocó el objeto que tenía la ventana


def test_se_puede_editar_un_evento_pasado_sin_tocar_la_fecha(app, guardar_evento):
    evento = guardar_evento("Viejo", dias=-5)
    app.editar_evento(evento)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    escribir(formulario._nombre, "Viejo corregido")

    formulario._guardar()
    esperar(app)

    assert service.obtener_evento(evento.id).nombre == "Viejo corregido"


def test_editar_un_evento_que_otro_ya_elimino_muestra_el_error(app, manana):
    evento = service.crear_evento(Evento("x", manana))
    app.editar_evento(evento)
    esperar(app)
    formulario = ventana_abierta(app, FormularioEvento)
    service.eliminar_evento(evento.id)  # desaparece mientras el formulario está abierto

    formulario._guardar()

    assert "no existe" in formulario._error.cget("text")
    assert contar_eventos() == 0


# --- detalle y eliminar ----------------------------------------------------------
def test_eliminar_pide_confirmacion(app, manana):
    evento = service.crear_evento(Evento("Borrar", manana))
    app.ver_evento(evento)
    esperar(app)
    detalle = ventana_abierta(app, DetalleEvento)

    detalle._eliminar()  # primer clic: solo pregunta

    assert contar_eventos() == 1
    assert "Confirmar" in detalle._boton_eliminar.cget("text")

    detalle._eliminar()  # segundo clic: borra
    esperar(app)

    assert contar_eventos() == 0
    assert ventana_abierta(app, DetalleEvento) is None


def test_cerrar_el_detalle_despues_del_primer_clic_no_elimina(app, manana):
    evento = service.crear_evento(Evento("Me arrepentí", manana))
    app.ver_evento(evento)
    esperar(app)
    detalle = ventana_abierta(app, DetalleEvento)

    detalle._eliminar()
    detalle.destroy()
    esperar(app, 100)

    assert contar_eventos() == 1


def test_eliminar_un_evento_que_ya_no_existe_muestra_el_error(app, manana):
    evento = service.crear_evento(Evento("x", manana))
    app.ver_evento(evento)
    esperar(app)
    detalle = ventana_abierta(app, DetalleEvento)
    service.eliminar_evento(evento.id)

    detalle._eliminar()
    detalle._eliminar()

    assert "no existe" in detalle._error.cget("text")


def test_el_detalle_de_un_evento_sin_hora_ni_descripcion_no_falla(app, manana):
    evento = service.crear_evento(Evento("Mínimo", manana))

    app.ver_evento(evento)
    esperar(app)

    assert ventana_abierta(app, DetalleEvento) is not None


def test_del_detalle_se_pasa_al_formulario_de_edicion(app, manana):
    evento = service.crear_evento(Evento("Editar", manana))
    app.ver_evento(evento)
    esperar(app)

    ventana_abierta(app, DetalleEvento)._editar()
    esperar(app)

    assert ventana_abierta(app, DetalleEvento) is None
    assert ventana_abierta(app, FormularioEvento)._nombre.get() == "Editar"


# --- lista del día ---------------------------------------------------------------
def test_la_lista_del_dia_lleva_la_grilla_a_ese_mes(app):
    app.ver_dia(date(2031, 3, 15))
    esperar(app)

    assert (app.anio, app.mes) == (2031, 3)
    assert ventana_abierta(app, EventosDelDia) is not None


def test_desde_la_lista_del_dia_se_crea_un_evento_en_esa_fecha(app, hoy):
    fecha = hoy + timedelta(days=40)
    app.ver_dia(fecha)
    esperar(app)

    ventana_abierta(app, EventosDelDia)._crear()
    esperar(app)

    assert ventana_abierta(app, FormularioEvento)._fecha.get() == fecha_a_texto(fecha)


# --- segundo plano (bandeja del sistema) ------------------------------------------
class BandejaDePrueba:
    """Ocupa el lugar del ícono real: anota lo que le piden y no muestra nada."""

    disponible = True  # False simula un sistema sin bandeja

    def __init__(self, al_abrir, al_crear, al_salir):
        self.al_abrir = al_abrir
        self.al_crear = al_crear
        self.al_salir = al_salir
        self.avisos = []
        self.detenida = False

    def iniciar(self):
        return self.disponible

    def avisar(self, mensaje):
        self.avisos.append(mensaje)

    def detener(self):
        self.detenida = True


@pytest.fixture
def con_bandeja(app, monkeypatch):
    monkeypatch.setattr(BandejaDePrueba, "disponible", True)
    monkeypatch.setattr(modulo_app, "IconoBandeja", BandejaDePrueba)
    assert app.activar_segundo_plano() is True
    return app._bandeja


def test_con_bandeja_la_x_oculta_la_ventana_sin_cerrar_la_app(app, con_bandeja):
    app.ocultar()  # lo que ejecuta la X
    esperar(app, 150)

    assert app.state() == "withdrawn"
    assert app.winfo_exists()
    assert con_bandeja.detenida is False


def test_al_ocultar_avisa_que_sigue_abierta_solo_la_primera_vez(app, con_bandeja):
    for _ in range(3):
        app.ocultar()
        app.mostrar()

    assert len(con_bandeja.avisos) == 1


def test_arrancar_en_segundo_plano_no_muestra_el_aviso(app, con_bandeja):
    app.ocultar(avisar=False)

    assert con_bandeja.avisos == []
    assert app.state() == "withdrawn"


def test_abrir_desde_la_bandeja_vuelve_a_mostrar_la_ventana(app, con_bandeja):
    app.ocultar()
    esperar(app, 100)

    con_bandeja.al_abrir()  # clic en "Abrir calendario"
    esperar(app, 500)

    assert app.state() == "normal"


def test_al_volver_a_mostrar_se_ven_los_eventos_creados_mientras_estaba_oculta(
    app, con_bandeja, guardar_evento, hoy
):
    app.ocultar()
    guardar_evento("Nuevo", dias=0)

    app.mostrar()
    esperar(app, 150)

    assert chips_de(app, hoy) == ["Nuevo"]


def test_nuevo_evento_desde_la_bandeja_muestra_la_ventana_y_el_formulario(
    app, con_bandeja
):
    app.ocultar()

    con_bandeja.al_crear()
    esperar(app, 600)

    assert app.state() == "normal"
    assert ventana_abierta(app, FormularioEvento) is not None


def test_los_pedidos_de_la_bandeja_llegan_bien_desde_otro_hilo(app, con_bandeja):
    # En la aplicación real, el menú del ícono corre en un hilo distinto al de
    # la ventana. Acá se piden 20 "abrir" seguidos desde otro hilo.
    app.ocultar()
    hilo = threading.Thread(target=lambda: [con_bandeja.al_abrir() for _ in range(20)])
    hilo.start()
    hilo.join()
    esperar(app, 600)

    assert app.state() == "normal"
    assert app._pedidos.empty()


def test_salir_desde_la_bandeja_quita_el_icono_y_cierra_la_ventana(app, con_bandeja):
    con_bandeja.al_salir()
    esperar_cierre = reloj.time() + 2
    while not app._cerrada and reloj.time() < esperar_cierre:
        app.update()
        reloj.sleep(0.01)

    assert app._cerrada is True
    assert con_bandeja.detenida is True
    with pytest.raises(tkinter.TclError):
        app.winfo_exists()  # la ventana ya no existe


def test_sin_bandeja_la_aplicacion_funciona_como_una_ventana_comun(app, monkeypatch):
    monkeypatch.setattr(BandejaDePrueba, "disponible", False)
    monkeypatch.setattr(modulo_app, "IconoBandeja", BandejaDePrueba)

    assert app.activar_segundo_plano() is False
    assert app._bandeja is None
    app.ocultar()  # aunque alguien la llame, no intenta avisar ni falla
    app.mostrar()
    app.salir()
    assert app._cerrada is True


def test_si_el_icono_no_se_puede_crear_iniciar_devuelve_false(monkeypatch):
    def falla(self):
        raise RuntimeError("este sistema no tiene bandeja")

    monkeypatch.setattr(modulo_bandeja.IconoBandeja, "_crear_icono", falla)
    icono = modulo_bandeja.IconoBandeja(lambda: None, lambda: None, lambda: None)

    assert icono.iniciar() is False
    icono.avisar("no falla aunque no haya ícono")
    icono.detener()


@pytest.mark.parametrize("tamano", [16, 32, 64, 256])
def test_la_imagen_del_icono_tiene_el_tamano_pedido(tamano):
    imagen = modulo_bandeja.crear_imagen(tamano)

    assert imagen.size == (tamano, tamano)
    assert imagen.mode == "RGBA"
