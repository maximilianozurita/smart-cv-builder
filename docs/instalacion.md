# Instalación

## Requisitos previos

- Python 3.10 o superior
- Al menos una API key de un proveedor LLM soportado
- **macOS**: Homebrew instalado
- **Windows**: [GTK3 Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) en el `PATH`
- **Linux**: `apt`/`dnf` disponible

---

## 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd smart-cv-builder
```

---

## 2. Crear y activar entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

---

## 3. Instalar dependencias del sistema (WeasyPrint)

WeasyPrint requiere librerías nativas para generar PDFs:

**macOS:**
```bash
brew install pango cairo gdk-pixbuf
```

**Ubuntu / Debian:**
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0
```

**Fedora / RHEL:**
```bash
sudo dnf install pango cairo gdk-pixbuf2
```

**Windows:** instalar [GTK3 para Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) y asegurarse de que el directorio `bin` esté en el `PATH`.

---

## 4. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

---

## 5. Configurar variables de entorno

```bash
cp .env.example .env
```

Completar `.env` con al menos una API key:

```env
GROQ_API_KEY=tu_key_aqui
GEMINI_API_KEY=tu_key_aqui
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# XAI_API_KEY=
```

### Dónde obtener las API keys

| Provider | URL | Costo |
|---|---|---|
| Gemini | https://aistudio.google.com/app/apikey | Gratis (sin tarjeta) |
| Groq | https://console.groq.com/keys | Free tier con cuota diaria |
| OpenAI | https://platform.openai.com/api-keys | De pago |
| Anthropic | https://console.anthropic.com/settings/keys | De pago |
| xAI | https://console.x.ai/ | De pago |

> Para empezar sin costo: **Gemini 2.5 Flash** (sin tarjeta) o **Groq** (Llama 3.3 70B, muy rápido).

---

## 6. Configurar datos del candidato

```bash
cp data/candidate_data.example.json data/candidate_data.json
```

Editar `data/candidate_data.json` con los datos reales. Campos principales:

| Campo | Descripción |
|---|---|
| `personal_info` | Nombre, email, teléfono, LinkedIn, ubicación |
| `summary_base` | Párrafo base del candidato (el LLM lo adapta al JD) |
| `technical_skills` | Dict de categoría → lista de skills |
| `experience` | Historial completo con responsabilidades, logros y tecnologías |
| `education` | Instituciones, títulos, años |
| `languages` | Idiomas con nivel |
| `certifications` | Opcional |

> Incluir la mayor cantidad de detalle posible en `experience.responsibilities` y `experience.achievements` — el LLM selecciona y adapta lo más relevante para cada JD.

---

## 7. Configurar roles

```bash
cp data/roles.example.json data/roles.json
```

Cada rol define el contexto que recibe el LLM para enfocar el CV. Campos relevantes: `display_name`, `focus_areas`, `prioritize_skills`, `bullet_style`, `experience_selection_criteria`.

Para agregar un nuevo rol: editar `data/roles.json` con la misma estructura que los existentes y recargar la página.

---

## 8. (Opcional) Agregar plantilla Word

Colocar `templates/cv_template.docx` con los macros `{{MACRO}}` correspondientes. También se puede subir desde la interfaz: **Settings → Word Template**.

Ver la lista completa de macros disponibles en [docs/arquitectura.md](arquitectura.md#macros-disponibles-para-la-plantilla-word).

---

## 9. Levantar la aplicación

**macOS / Linux:**
```bash
./run_web.sh
```

> El script activa el entorno virtual y configura `DYLD_LIBRARY_PATH` para que WeasyPrint encuentre las librerías de Homebrew en macOS.

**Windows:**
```bash
.venv\Scripts\activate
uvicorn web.main:app --reload --port 8000
```

Abrir en el navegador: **http://localhost:8000**

---

## Verificar que funciona

1. Abrir `http://localhost:8000` — debe aparecer la interfaz con 3 paneles
2. Activar **Dry run** en el panel izquierdo
3. Escribir cualquier texto en **Job Description** y hacer clic en **✨ Generate CV**
4. El preview debe actualizarse con un CV de ejemplo sin llamar al LLM

---

## CLI (alternativa a la web)

```bash
python generate_cv.py --role backend_engineer --jd job_description.txt --provider groq
```

Los CVs generados se guardan en `output/`.
