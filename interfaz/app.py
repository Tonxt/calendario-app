import customtkinter as ctk
from datetime import date

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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calendario")
        self.geometry("900x600")
        self.barra_lateral = ctk.CTkFrame(self, fg_color="gray15", width=220)
        self.barra_superior = ctk.CTkFrame(self, fg_color="gray20", height=60)
        self.grilla = ctk.CTkFrame(self, fg_color="gray25")
        self.barra_lateral.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.barra_superior.grid(row=0, column=1, sticky="nsew")
        self.grilla.grid(row=1, column=1, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.anio = date.today().year
        self.mes = date.today().month
        ctk.CTkButton(
            self.barra_superior, text="Hoy", width=40, command=self.ir_a_hoy
        ).grid(row=0, column=0, padx=5, pady=10)
        ctk.CTkButton(
            self.barra_superior, text="◀", width=40, command=self.mes_anterior
        ).grid(row=0, column=1, padx=5, pady=10)
        ctk.CTkButton(
            self.barra_superior, text="▶", width=40, command=self.mes_siguiente
        ).grid(row=0, column=2, padx=5, pady=10)
        self.titulo_mes = ctk.CTkLabel(
            self.barra_superior,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.titulo_mes.grid(row=0, column=3, padx=5, pady=10)
        self._actualizar_titulo()

    def _actualizar_titulo(self):
        self.titulo_mes.configure(text=f"{MESES[self.mes-1]} {self.anio}")

    def mes_siguiente(self):
        if self.mes == 12:
            self.mes = 1
            self.anio += 1
        else:
            self.mes += 1
        self._actualizar_titulo()

    def mes_anterior(self):
        if self.mes == 1:
            self.mes = 12
            self.anio -= 1
        else:
            self.mes -= 1
        self._actualizar_titulo()

    def ir_a_hoy(self):
        self.anio = date.today().year
        self.mes = date.today().month
        self._actualizar_titulo()
