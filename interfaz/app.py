import customtkinter as ctk


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
