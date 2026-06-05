# 🛠️ Plan de Desarrollo — Vader_Brain

Este documento registra el estado técnico del proyecto, las debilidades detectadas,
las correcciones aplicadas y la hoja de ruta pendiente.

---

## 1. Estado general

Vader_Brain orquesta tres motores:

- **Ollama** (local) → clasificación de intenciones y tareas simples.
- **Gemini / ChatGPT vía Selenium** → generación compleja y Deep Research.
- **Generadores Office** (`python-docx`, `openpyxl`, `python-pptx`) → Word/Excel/PPT.

Flujo: `gui.py` → `dispatcher_ia()` (`tools/ai_tools.py`) → comandos → `web_ai_tools.py` → generadores.

---

## 2. Revisión y debilidades detectadas (2026-05)

### 🔴 Críticas
1. **Parsing de JSON frágil.** `limpiar_json_de_chatgpt` solo quitaba vallas markdown;
   cualquier texto introductorio rompía `json.loads` → fallo total de la generación.
2. **Login de ChatGPT no detectado.** Solo se detectaba el login de Google; el redirect
   a `auth.openai.com` y los retos de Cloudflare dejaban al bot esperando indefinidamente.
3. **GUI congelada.** El dispatcher corría en el hilo principal de Tkinter (la ventana
   quedaba "No responde" durante todo el Deep Research, sin feedback).
4. **Navegación poco resiliente** en Deep Research (cada sección recarga toda la página).

### 🟠 Importantes
5. **`taskkill` mataba TODOS los Chrome** del usuario (pérdida de pestañas/trabajo).
6. **Inconsistencias README ↔ código** (entorno conda `vader` vs `agente_ia`, `templates/`
   documentada pero no usada, `pandas` listada pero no importada).
7. **Sin guardas** ante respuestas vacías, nombres de archivo vacíos o JSON malformado.

### 🟡 Menores
8. Detección de fin de respuesta solo por estabilidad de texto (heurística).
9. Autofit de Excel ignoraba columnas numéricas.
10. Perfil de Chrome en el Escritorio.
11. Imports a mitad de archivo / imports no usados.
12. Configuración hardcodeada (sin `.env`).
13. Sin plan de desarrollo en el repo.
14. Ollama se invocaba en cada request aunque las keywords fueran obvias.

---

## 3. Correcciones aplicadas ✅

| # | Corrección | Archivos |
|---|---|---|
| 1 | Parser de JSON tolerante: recorta por corchetes balanceados, ignora prosa y vallas, corrige comas finales (`parsear_json_ia`). | `tools/ai_tools.py` |
| 2 | Detección de login de Google **y** OpenAI/ChatGPT + manejo de Cloudflare, con espera de login manual. | `tools/web_ai_tools.py` |
| 3 | GUI ejecuta el dispatcher en un **hilo aparte** y vuelca el progreso (`print`) en vivo a la consola. | `gui.py` |
| 4 | Detección de fin por **desaparición del botón "stop"** + estabilidad de texto. | `tools/web_ai_tools.py` |
| 5 | Solo se cierran los Chrome que usan **el perfil del bot** (PowerShell filtrado por CommandLine). | `tools/web_ai_tools.py` |
| 6 | README alineado: entorno `agente_ia`, `templates/` marcada como reservada, `pandas`→`python-dotenv`. | `README.md`, `requirements.txt` |
| 7 | Guardas: nombre vacío → `documento`; workbook sin hojas no rompe openpyxl; ítems no-dict ignorados. | `tools/ai_tools.py`, `tools/excel_tools.py` |
| 9 | Autofit de Excel usa `str(valor)` y limita el ancho máximo a 60. | `tools/excel_tools.py` |
| 10 | Perfil de Chrome en `%LOCALAPPDATA%\VaderBrain` (configurable). | `config.py` |
| 11 | Imports movidos al inicio; eliminados `Emu`, `textwrap`, `qn`/`etree` sin uso; `MSO_SHAPE`. | `main.py`, `tools/ppt_tools.py` |
| 12 | Configuración central por `.env` (`OLLAMA_*`, `MOTOR_IA_DEFECTO`, timeouts, perfil). | `config.py`, `.env.example` |
| 13 | Este documento. | `DESARROLLO.md` |
| 14 | Clasificación **keyword-first**; Ollama solo se consulta si las keywords no resuelven el tipo. | `tools/ai_tools.py` |

Transliteración de acentos en nombres de archivo (á→a, ñ→n) para no perder palabras.

---

## 3b. Skill nueva: Copiador de formato Word (`format_tools.py`)

Aplica el formato de un documento **ejemplo** a un documento **destino** ya escrito.

- **Modo híbrido** de identificación: usa los estilos de Word del destino si existen
  (Título, Subtítulo, Encabezado 1-3) y, si no, los detecta por heurística (tamaño de
  fuente relativo al cuerpo, negrita, longitud de línea y numeración `1.` / `1.1` / `1.1.1`).
- **Copia completa** de formato: definiciones de estilo (`w:style`) + `docDefaults`,
  márgenes y configuración de página, y estilo de tablas. El destino se renderiza con el
  look exacto del ejemplo.
- **Flujo de carpetas:** ejemplo en `templates/`, destino en `inputs/`, salida en `outputs/`.
- **Dispatcher:** keywords `copia/aplica/usa el formato …` → `cmd_copiar_formato_word`,
  evaluado antes del enrutamiento por tipo para no crear un documento nuevo.

**Limitación conocida:** la heurística sobre texto plano (sin estilos) acierta en la
mayoría de casos pero no es infalible; para control exacto, marcar los títulos del destino
con estilos de Word. (En la hoja de ruta: botón en la GUI con dos selectores de archivo.)

---

## 4. Hoja de ruta (pendiente)

### Corto plazo
- [ ] **Reintentos automáticos** por sección en Deep Research (1–2 reintentos antes de saltar).
- [ ] **Reutilizar la conversación** de Gemini/ChatGPT entre secciones en vez de recargar la
      página cada vez (más rápido y con contexto compartido).
- [ ] **Barra de progreso** real en la GUI (X/Y secciones) además del log de texto.
- [ ] Botón de **cancelar** la tarea en curso.
- [ ] **Botón de GUI para el copiador de formato** (dos selectores de archivo: ejemplo + destino).
- [ ] Mejorar la heurística del copiador (detección de listas y de subtítulo vs. título).

### Medio plazo
- [ ] **Tests unitarios** del parser JSON, el sanitizador de nombres y los generadores Office.
- [ ] **Caché de respuestas** de IA por prompt (evita repetir llamadas caras al reintentar).
- [ ] Selectores de UI de Gemini/ChatGPT **externalizados** a un archivo de config para
      adaptarse rápido a cambios de Google/OpenAI sin tocar el código.
- [ ] Soporte de **PDF** (ya documentado como ejemplo en el README).

### Largo plazo
- [ ] Migrar de scraping web a **APIs oficiales** (Gemini API / OpenAI API) como opción,
      manteniendo Selenium como fallback gratuito.
- [ ] Exportación combinada (p. ej. Word con tabla de Excel embebida).
- [ ] Plantillas APA/IEEE seleccionables y carpeta `templates/` funcional.

---

## 5. Riesgos conocidos

- **Fragilidad del scraping:** los selectores CSS de Gemini/ChatGPT cambian sin aviso.
  Mitigado con múltiples selectores candidatos, pero requiere mantenimiento periódico.
- **Verificación de referencias APA:** las referencias las genera la IA y **pueden ser
  inexactas**. El documento incluye un disclaimer; conviene verificarlas antes de publicar.
- **Cloudflare / rate limits:** sesiones intensivas de Deep Research pueden disparar retos
  o límites. El bot espera, pero no los elude.
