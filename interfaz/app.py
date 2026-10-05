"""Ventana principal de la aplicación."""

import queue
from datetime import date

import customtkinter as ctk

from backend import service
from backend.models import Evento
from interfaz.bandeja import IconoBandeja
from interfaz.barra_lateral import BarraLateral
from interfaz.dialogos import DetalleEvento, EventosDelDia
from interfaz.estilos import COLOR_FONDO, COLOR_PANEL, boton_secundario, fuente
from interfaz.formato import titulo_mes
from interfaz.formulario_evento import FormularioEvento
from interfaz.vista_calendario import VistaCalendario, semanas_del_mes

MINUTO_EN_MS = 60_000
REVISAR_PEDIDOS_CADA_MS = 200


class App(ctk.CTk):
    """Ventana principal: coordina las tres zonas y habla con el service.

    Es la única clase de la interfaz que le pide datos al backend para
    mostrarlos. Las demás zonas reciben los datos ya buscados y le avisan a
    esta ventana, mediante funciones, lo que hace el usuario.
    """

    def __init__(self):
        ctk.set_appearance_mode("dark")  # los colores están pensados para fondo oscuro
        super().__init__(fg_color=COLOR_FONDO)
        self.title("Calendario")
        self.geometry("1100x700")
        self.minsize(820, 560)

        # Estado: qué mes se está mostrando.
        self.anio = date.today().year
        self.mes = date.today().month
        self._ultimo_dia_dibujado = date.today()

        # Segundo plano (se activa con activar_segundo_plano).
        self._bandeja: IconoBandeja | None = None
        self._ya_aviso_que_sigue_abierta = False
        self._cerrada = False
        # Cola de pedidos que llegan desde otros hilos (el ícono de la bandeja).
        self._pedidos: queue.Queue = queue.Queue()

        # Las tres zonas de la ventana.
        self.barra_lateral = BarraLateral(
            self,
            al_crear=self.nuevo_evento,
            al_elegir_dia=self.ver_dia,
            al_elegir_evento=self.ver_evento,
            fechas_con_eventos=self._fechas_con_eventos,
        )
        self.barra_superior = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_PANEL)
        self.grilla = VistaCalendario(
            self,
            al_elegir_dia=self.nuevo_evento,
            al_elegir_evento=self.ver_evento,
            al_ver_mas=self.ver_dia,
        )
        self.barra_lateral.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.barra_superior.grid(row=0, column=1, sticky="nsew")
        self.grilla.grid(row=1, column=1, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Barra superior: navegación entre meses.
        boton_secundario(self.barra_superior, "Hoy", self.ir_a_hoy, width=64).grid(
            row=0, column=0, padx=(16, 8), pady=12
        )
        boton_secundario(self.barra_superior, "◀", self.mes_anterior, width=36).grid(
            row=0, column=1, padx=2, pady=12
        )
        boton_secundario(self.barra_superior, "▶", self.mes_siguiente, width=36).grid(
            row=0, column=2, padx=2, pady=12
        )
        self.titulo_mes = ctk.CTkLabel(
            self.barra_superior, text="", font=fuente(20, negrita=True)
        )
        self.titulo_mes.grid(row=0, column=3, padx=14, pady=12)

        # Atajos de teclado.
        self.bind("<Left>", lambda evento_tk: self.mes_anterior())
        self.bind("<Right>", lambda evento_tk: self.mes_siguiente())

        self.actualizar_vista()
        self.after(MINUTO_EN_MS, self._revisar_cambio_de_dia)
        self.after(REVISAR_PEDIDOS_CADA_MS, self._atender_pedidos)

    # --- Dibujo ----------------------------------------------------------------
    def _actualizar_titulo(self):
        self.titulo_mes.configure(text=titulo_mes(self.anio, self.mes))

    def actualizar_vista(self):
        """Vuelve a pedirle los datos al service y redibuja todo.

        Se llama al cambiar de mes y después de crear, editar o eliminar un
        evento, para que la pantalla siempre muestre lo que hay en la base.
        """
        self._actualizar_titulo()
        self.grilla.mostrar(self.anio, self.mes, self._eventos_visibles())
        self.barra_lateral.mini_calendario.mostrar(self.anio, self.mes)
        self.barra_lateral.mostrar_eventos_de_hoy(service.eventos_del_dia(date.today()))
        self._ultimo_dia_dibujado = date.today()

    def _eventos_visibles(self) -> dict[date, list[Evento]]:
        """Los eventos de todas las fechas que se ven en la grilla, por fecha.

        La grilla también muestra los últimos días del mes anterior y los
        primeros del siguiente, así que puede haber que consultar hasta tres
        meses.
        """
        # Un conjunto (set) no guarda repetidos: quedan solo los meses distintos.
        meses = {
            (fecha.year, fecha.month)
            for semana in semanas_del_mes(self.anio, self.mes)
            for fecha in semana
        }
        eventos_por_fecha: dict[date, list[Evento]] = {}
        for anio, mes in sorted(meses):
            for evento in service.eventos_del_mes(anio, mes):
                # setdefault devuelve la lista de esa fecha y, si todavía no
                # existe, la crea vacía.
                eventos_por_fecha.setdefault(evento.fecha, []).append(evento)
        return eventos_por_fecha

    def _fechas_con_eventos(self, anio: int, mes: int) -> set[date]:
        """Las fechas de ese mes que tienen algún evento (para el mini calendario)."""
        return {evento.fecha for evento in service.eventos_del_mes(anio, mes)}

    def _revisar_cambio_de_dia(self):
        # Si la app queda abierta de un día para el otro, a la medianoche hay
        # que mover la marca de "hoy" y la lista de eventos de hoy.
        if date.today() != self._ultimo_dia_dibujado:
            self.actualizar_vista()
        self.after(MINUTO_EN_MS, self._revisar_cambio_de_dia)
        self.after(REVISAR_PEDIDOS_CADA_MS, self._atender_pedidos)

    # --- Navegación ------------------------------------------------------------
    def mes_siguiente(self):
        if self.mes == 12:
            self.mes = 1
            self.anio += 1
        else:
            self.mes += 1
        self.actualizar_vista()

    def mes_anterior(self):
        if self.mes == 1:
            self.mes = 12
            self.anio -= 1
        else:
            self.mes -= 1
        self.actualizar_vista()

    def ir_a_hoy(self):
        self.ir_a_fecha(date.today())

    def ir_a_fecha(self, fecha: date):
        if (fecha.year, fecha.month) != (self.anio, self.mes):
            self.anio = fecha.year
            self.mes = fecha.month
        self.actualizar_vista()

    # --- Acciones del usuario --------------------------------------------------
    def nuevo_evento(self, fecha: date | None = None):
        """Abre el formulario vacío. Con `fecha`, ese día ya viene cargado."""
        FormularioEvento(self, al_guardar=self.actualizar_vista, fecha_inicial=fecha)

    def editar_evento(self, evento: Evento):
        FormularioEvento(self, al_guardar=self.actualizar_vista, evento=evento)

    def ver_evento(self, evento: Evento):
        """Abre el detalle de un evento, con las opciones de editar y eliminar."""
        DetalleEvento(
            self,
            evento,
            al_editar=self.editar_evento,
            al_eliminar=self.actualizar_vista,
        )

    def ver_dia(self, fecha: date):
        """Lleva la grilla al mes de esa fecha y lista los eventos de ese día."""
        self.ir_a_fecha(fecha)
        EventosDelDia(
            self,
            fecha,
            service.eventos_del_dia(fecha),
            al_elegir_evento=self.ver_evento,
            al_crear=self.nuevo_evento,
        )

    # --- Segundo plano -----------------------------------------------------------
    def activar_segundo_plano(self) -> bool:
        """Pone el ícono en la bandeja y hace que la X oculte en vez de cerrar.

        Devuelve False si el sistema no tiene bandeja. En ese caso no cambia
        nada: la X cierra la aplicación, como en cualquier ventana.
        """
        # El ícono corre en otro hilo y tkinter solo se puede usar desde el
        # hilo de la ventana. Por eso el menú del ícono no llama a los métodos
        # directamente: deja el pedido en una cola, que es segura entre hilos,
        # y la ventana lo atiende desde su propio hilo.
        bandeja = IconoBandeja(
            al_abrir=lambda: self._pedidos.put(self.mostrar),
            al_crear=lambda: self._pedidos.put(self.mostrar_y_crear),
            al_salir=lambda: self._pedidos.put(self.salir),
        )
        if not bandeja.iniciar():
            return False
        self._bandeja = bandeja
        # WM_DELETE_WINDOW es el aviso que manda el sistema al tocar la X.
        self.protocol("WM_DELETE_WINDOW", self.ocultar)
        return True

    def _atender_pedidos(self):
        try:
            while not self._cerrada:
                pedido = self._pedidos.get_nowait()
                pedido()
        except queue.Empty:
            pass
        if not self._cerrada:  # si el pedido fue "salir", ya no hay ventana
            self.after(REVISAR_PEDIDOS_CADA_MS, self._atender_pedidos)

    def ocultar(self, avisar: bool = True):
        """Esconde la ventana; la aplicación y los recordatorios siguen activos."""
        self.withdraw()
        if (
            avisar
            and self._bandeja is not None
            and not self._ya_aviso_que_sigue_abierta
        ):
            self._ya_aviso_que_sigue_abierta = True  # solo la primera vez
            self._bandeja.avisar(
                "Calendario sigue abierto acá para avisarte de tus eventos. "
                "Para cerrarlo del todo, clic derecho y Salir."
            )

    def mostrar(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.actualizar_vista()  # mientras estuvo oculta pudo haber cambiado el día

    def mostrar_y_crear(self):
        self.mostrar()
        self.nuevo_evento()

    def salir(self):
        """Cierra la aplicación de verdad."""
        self._cerrada = True
        if self._bandeja is not None:
            self._bandeja.detener()
            self._bandeja = None
        self.destroy()
