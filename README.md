# Calendario App

Aplicación de escritorio en Python para agendar eventos y recibir recordatorios en la computadora.

## Estructura

```
calendario-app/
├── main.py                  # Punto de entrada
├── backend/                 # Lógica y datos (no sabe nada de la interfaz)
│   ├── models.py            # Entidad Evento
│   ├── database.py          # Conexión y tablas SQLite
│   ├── repository.py        # CRUD de eventos
│   ├── service.py           # Reglas de negocio (puerta de entrada al backend)
│   ├── scheduler.py         # Programación de recordatorios
│   └── notifier.py          # Notificaciones del sistema
├── interfaz/                # Todo lo visual
│   ├── app.py               # Ventana principal
│   ├── vista_calendario.py  # Calendario mensual
│   └── formulario_evento.py # Crear / editar eventos
├── data/                    # Acá vive la base de datos (ignorada por git)
└── tests/                   # Pruebas del backend
```

## Reglas de arquitectura

1. `interfaz/` solo habla con `backend/service.py`, nunca con el repositorio ni con la base de datos.
2. `backend/` nunca importa nada de `interfaz/`.
3. El flujo es: interfaz → service → repository → database.

## Etapas

- [ ] 1. Backend por consola: agregar, listar y borrar eventos en SQLite
- [ ] 2. Recordatorios con notificaciones del sistema
- [ ] 3. Interfaz gráfica
- [ ] 4. Segundo plano (bandeja del sistema y arranque automático)
- [ ] 5. Extras (eventos repetidos, categorías, exportar a .ics)
