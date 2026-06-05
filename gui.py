import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import sys
import threading
import queue
from main import (
    cmd_listar, cmd_leer, cmd_crear_docx_profesional,
    cmd_escribir_excel, cmd_actualizar_ppt, ask_ollama
)
from tools.ai_tools import dispatcher_ia


class _RedirectorConsola:
    """Redirige la salida estándar (print) a una cola para mostrarla en la GUI."""

    def __init__(self, cola: queue.Queue):
        self.cola = cola

    def write(self, texto: str):
        if texto:
            self.cola.put(texto)

    def flush(self):
        pass

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AgenteArchivosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vader_Brain")
        self.geometry("900x700")

        # --- Variables de estado ---
        self.archivo_seleccionado = ctk.StringVar(value="")
        self.tipo_archivo = ctk.StringVar(value="Word")

        # Cola para el progreso en vivo desde el hilo de trabajo
        self.cola_log = queue.Queue()
        self._procesando = False

        self.crear_widgets()
        self._procesar_cola_log()

    def crear_widgets(self):
        # --- Panel Izquierdo: Controles ---
        self.panel_izq = ctk.CTkFrame(self, width=300)
        self.panel_izq.pack(side="left", fill="y", padx=10, pady=10)

        # Título Panel Izq
        ctk.CTkLabel(self.panel_izq, text="Panel de Control", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # Seleccionar Archivo
        ctk.CTkLabel(self.panel_izq, text="Archivo seleccionado:").pack(anchor="w", padx=10, pady=(10, 0))
        self.entry_archivo = ctk.CTkEntry(self.panel_izq, textvariable=self.archivo_seleccionado, width=200, state="disabled")
        self.entry_archivo.pack(padx=10, pady=5)

        self.btn_seleccionar = ctk.CTkButton(self.panel_izq, text="Seleccionar Archivo", command=self.seleccionar_archivo)
        self.btn_seleccionar.pack(padx=10, pady=5)

        # Selector de Tipo
        ctk.CTkLabel(self.panel_izq, text="Tipo de Archivo:").pack(anchor="w", padx=10, pady=(15, 0))
        self.combo_tipo = ctk.CTkComboBox(self.panel_izq, values=["Word", "Excel", "PowerPoint", "Texto"], variable=self.tipo_archivo)
        self.combo_tipo.pack(padx=10, pady=5)

        # Botones de Acciones Rápidas
        ctk.CTkLabel(self.panel_izq, text="Acciones Rápidas:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(20, 5))

        self.btn_listar = ctk.CTkButton(self.panel_izq, text="Listar Archivos (outputs)", command=self.accion_listar)
        self.btn_listar.pack(padx=10, pady=5, fill="x")

        self.btn_leer = ctk.CTkButton(self.panel_izq, text="Leer Archivo Seleccionado", command=self.accion_leer)
        self.btn_leer.pack(padx=10, pady=5, fill="x")

        # --- Panel Derecho: Instrucciones y Consola ---
        self.panel_der = ctk.CTkFrame(self)
        self.panel_der.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        # Input de Instrucciones
        ctk.CTkLabel(self.panel_der, text="Instrucciones para la IA:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=10)

        self.texto_input = ctk.CTkTextbox(self.panel_der, height=100)
        self.texto_input.pack(fill="x", padx=10, pady=5)

        # Botones Ejecutar
        frame_botones = ctk.CTkFrame(self.panel_der, fg_color="transparent")
        frame_botones.pack(pady=10)

        self.btn_ejecutar_accion = ctk.CTkButton(frame_botones, text="Ejecutar Acción", command=self.ejecutar_accion, fg_color="#1E90FF", hover_color="#0000CD")
        self.btn_ejecutar_accion.pack(side="left", padx=5)

        self.btn_ejecutar_ia = ctk.CTkButton(frame_botones, text="Generar con IA", command=self.ejecutar_ia, fg_color="green", hover_color="dark green")
        self.btn_ejecutar_ia.pack(side="left", padx=5)

        # Consola de Salida
        ctk.CTkLabel(self.panel_der, text="Consola de Salida:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.consola = ctk.CTkTextbox(self.panel_der, state="disabled", wrap="word")
        self.consola.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    def log(self, mensaje):
        """Añade un mensaje a la consola de salida."""
        self.consola.configure(state="normal")
        self.consola.insert("end", mensaje + "\n\n")
        self.consola.see("end")
        self.consola.configure(state="disabled")

    def _log_raw(self, texto):
        """Inserta texto sin saltos extra (usado para el progreso en vivo)."""
        self.consola.configure(state="normal")
        # '\r' (retorno de carro) se usa para barras de progreso; lo normalizamos
        self.consola.insert("end", texto.replace("\r", "\n"))
        self.consola.see("end")
        self.consola.configure(state="disabled")

    def _procesar_cola_log(self):
        """Vacía periódicamente la cola de progreso hacia la consola de la GUI."""
        try:
            while True:
                texto = self.cola_log.get_nowait()
                self._log_raw(texto)
        except queue.Empty:
            pass
        self.after(100, self._procesar_cola_log)

    def seleccionar_archivo(self):
        filepath = filedialog.askopenfilename(initialdir="outputs", title="Seleccionar Archivo")
        if filepath:
            filename = os.path.basename(filepath)
            self.archivo_seleccionado.set(filename)
            self.log(f"Archivo seleccionado: {filename}")

    def accion_listar(self):
        self.log("Listando archivos en 'outputs'...")
        resultado = cmd_listar("outputs")
        self.log(resultado)

    def accion_leer(self):
        filename = self.archivo_seleccionado.get()
        if not filename:
            self.log("Error: Selecciona un archivo primero.")
            return
        self.log(f"Leyendo '{filename}'...")
        resultado = cmd_leer(filename)
        self.log(resultado)

    def ejecutar_accion(self):
        """Ejecuta una acción manual según el tipo de archivo seleccionado."""
        filename = self.archivo_seleccionado.get()
        tipo = self.tipo_archivo.get()

        self.log(f"Ejecutando acción manual para '{filename}' ({tipo})...")
        if not filename:
             self.log("Advertencia: No hay archivo seleccionado, ejecutando acción genérica por tipo.")

        if tipo == "Word":
             self.log("Función de acción Word: Falta implementar lógica manual o puedes usar el dispatcher IA.")
        elif tipo == "Excel":
             self.log("Función de acción Excel: Falta implementar lógica manual o puedes usar el dispatcher IA.")
        elif tipo == "PowerPoint":
             self.log("Función de acción PowerPoint: Falta implementar lógica manual o puedes usar el dispatcher IA.")
        else:
             self.log(f"Acción no definida para {tipo}.")

    def ejecutar_ia(self):
        if self._procesando:
            self.log("Ya hay una tarea en curso. Espera a que termine.")
            return

        instruccion = self.texto_input.get("1.0", "end-1c").strip()
        if not instruccion:
            self.log("Error: Ingresa una instrucción para la IA.")
            return

        self.log(f"Enviando instrucción al Dispatcher IA:\n-> {instruccion}")
        self._procesando = True
        self.btn_ejecutar_ia.configure(state="disabled", text="Procesando...")

        # Ejecutar en un hilo aparte para no congelar la GUI.
        hilo = threading.Thread(target=self._tarea_ia, args=(instruccion,), daemon=True)
        hilo.start()

    def _tarea_ia(self, instruccion):
        """Corre en un hilo de fondo: redirige print() a la consola y ejecuta el dispatcher."""
        stdout_original = sys.stdout
        sys.stdout = _RedirectorConsola(self.cola_log)
        try:
            resultado = dispatcher_ia(instruccion)
            self.cola_log.put(f"\n\nResultado IA:\n{resultado}\n\n")
        except Exception as e:
            self.cola_log.put(f"\n\nError en ejecución IA: {e}\n\n")
        finally:
            sys.stdout = stdout_original
            # Reactivar el botón desde el hilo de la GUI
            self.after(0, self._finalizar_tarea_ia)

    def _finalizar_tarea_ia(self):
        self._procesando = False
        self.btn_ejecutar_ia.configure(state="normal", text="Generar con IA")

if __name__ == "__main__":
    app = AgenteArchivosApp()
    app.mainloop()
