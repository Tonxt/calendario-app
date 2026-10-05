"""Formulario para crear o editar un evento."""

from datetime import date

import customtkinter as ctk

from backend import service
from backend.models import Evento
from interfaz.estilos import (
    COLOR_BORDE,
    COLOR_CAMPO,
    COLOR_ERROR,
    COLOR_TEXTO,
    COLOR_TEXTO_TENUE,
    boton_principal,
    boton_secundario,
    fuente,
)
from interfaz.formato import fecha_a_texto, hora_a_texto, texto_a_fecha, texto_a_hora
from interfaz.modal import VentanaModal


class FormularioEvento(VentanaModal):
    """Ventana para cargar los datos de un evento.

    Si recibe un `evento`, lo edita. Si no, crea uno nuevo, con
    `fecha_inicial` ya escrita en el campo de fecha.

    Reparto de tareas con el backend:
    - La interfaz convierte los textos del usuario a `date` y `time`.
    - El service decide si los datos son válidos y los guarda.
    """

    def __init__(
        self,
        master,
        al_guardar,
        evento: Evento | None = None,
        fecha_inicial: date | None = None,
    ):
        titulo = "Nuevo evento" if evento is None else "Editar evento"
        super().__init__(master, titulo, ancho=440, alto=470)
        self._al_guardar = al_guardar
        self._evento = evento

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=24, pady=20)
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            cuerpo, text=titulo, anchor="w", font=fuente(18, negrita=True)
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        self._nombre = self._campo(cuerpo, "Nombre", fila=1, columna=0, columnas=2)
        self._nombre.configure(placeholder_text="Por ejemplo: Parcial de Cálculo")
        self._fecha = self._campo(cuerpo, "Fecha", fila=3, columna=0)
        self._fecha.configure(placeholder_text="dd/mm/aaaa")
        self._hora = self._campo(cuerpo, "Hora (opcional)", fila=3, columna=1)
        self._hora.configure(placeholder_text="hh:mm")

        self._etiqueta(cuerpo, "Descripción (opcional)").grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(12, 4)
        )
        self._descripcion = ctk.CTkTextbox(
            cuerpo,
            height=96,
            fg_color=COLOR_CAMPO,
            border_color=COLOR_BORDE,
            border_width=1,
            text_color=COLOR_TEXTO,
            font=fuente(13),
            wrap="word",
        )
        self._descripcion.grid(row=6, column=0, columnspan=2, sticky="ew")

        self._error = ctk.CTkLabel(
            cuerpo,
            text="",
            anchor="w",
            justify="left",
            wraplength=390,
            text_color=COLOR_ERROR,
            font=fuente(12),
        )
        self._error.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        botones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        botones.grid(row=8, column=0, columnspan=2, sticky="e", pady=(10, 0))
        boton_secundario(botones, "Cancelar", self.destroy, width=100).grid(
            row=0, column=0, padx=(0, 8)
        )
        boton_principal(botones, "Guardar", self._guardar, width=110).grid(
            row=0, column=1
        )

        self._cargar_datos_iniciales(fecha_inicial)

        # Enter guarda desde los campos de una sola línea. En la descripción,
        # Enter tiene que seguir haciendo un salto de línea.
        for campo in (self._nombre, self._fecha, self._hora):
            campo.bind("<Return>", lambda evento_tk: self._guardar())

    # --- Construcción ----------------------------------------------------------
    def _etiqueta(self, master, texto: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(
            master,
            text=texto,
            anchor="w",
            text_color=COLOR_TEXTO_TENUE,
            font=fuente(12),
        )

    def _campo(
        self, master, texto: str, fila: int, columna: int, columnas: int = 1
    ) -> ctk.CTkEntry:
        """Crea una etiqueta con su campo de texto debajo y devuelve el campo."""
        # Separación entre las dos columnas (Fecha a la izquierda, Hora a la derecha).
        if columnas == 2:
            margen = 0
        elif columna == 0:
            margen = (0, 6)
        else:
            margen = (6, 0)
        self._etiqueta(master, texto).grid(
            row=fila,
            column=columna,
            columnspan=columnas,
            sticky="ew",
            padx=margen,
            pady=(12 if fila > 1 else 0, 4),
        )
        campo = ctk.CTkEntry(
            master,
            height=36,
            fg_color=COLOR_CAMPO,
            border_color=COLOR_BORDE,
            border_width=1,
            text_color=COLOR_TEXTO,
            font=fuente(13),
        )
        campo.grid(
            row=fila + 1, column=columna, columnspan=columnas, sticky="ew", padx=margen
        )
        return campo

    def _cargar_datos_iniciales(self, fecha_inicial: date | None) -> None:
        if self._evento is None:
            self._fecha.insert(0, fecha_a_texto(fecha_inicial or date.today()))
            return
        self._nombre.insert(0, self._evento.nombre)
        self._fecha.insert(0, fecha_a_texto(self._evento.fecha))
        self._hora.insert(0, hora_a_texto(self._evento.hora))
        if self._evento.descripcion:
            self._descripcion.insert("1.0", self._evento.descripcion)

    def al_abrir(self) -> None:
        self._nombre.focus_set()

    # --- Guardado --------------------------------------------------------------
    def _guardar(self) -> None:
        self._error.configure(text="")

        # 1. Pasar los textos a los tipos que espera el backend.
        try:
            fecha = texto_a_fecha(self._fecha.get())
            hora = texto_a_hora(self._hora.get())
        except ValueError as error:
            self._error.configure(text=str(error))
            return
        # "1.0" es el principio del texto y "end-1c" el final sin el salto de
        # línea que el cuadro de texto agrega solo.
        descripcion = self._descripcion.get("1.0", "end-1c").strip() or None

        # 2. Armar el evento. Al editar se crea una copia: si el service la
        # rechaza, el evento original queda intacto.
        if self._evento is None:
            evento = Evento(
                self._nombre.get(), fecha, hora=hora, descripcion=descripcion
            )
        else:
            evento = Evento(
                self._nombre.get(),
                fecha,
                id=self._evento.id,
                hora=hora,
                descripcion=descripcion,
                aviso_previo_enviado=self._evento.aviso_previo_enviado,
                aviso_dia_enviado=self._evento.aviso_dia_enviado,
            )

        # 3. El service valida y guarda. Si alguna regla no se cumple, lanza
        # ErrorValidacion con el mensaje para mostrarle al usuario.
        try:
            if self._evento is None:
                service.crear_evento(evento)
            else:
                service.actualizar_evento(evento)
        except service.ErrorValidacion as error:
            self._error.configure(text=str(error))
            return

        self.destroy()
        self._al_guardar()
