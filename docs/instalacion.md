# Instalación

## Requisitos previos

- Python 3.10 o superior (para instalación local)
- Docker y Docker Compose (para instalación con contenedor)
- Al menos una API key de un proveedor LLM soportado
- **macOS**: Homebrew instalado (para instalación local)
- **Windows**: [GTK3 Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) en el `PATH` (para instalación local)
- **Linux**: `apt`/`dnf` disponible (para instalación local)

---

## Opción A: Instalación local

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd smart-cv-builder
```

---

### 2. Crear y activar entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

---

### 3. Instalar dependencias del sistema (WeasyPrint)

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

### 4. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

---

### 5. Configurar variables de entorno

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

#### Dónde obtener las API keys

| Provider | URL | Costo |
|---|---|---|
| Gemini | https://aistudio.google.com/app/apikey | Gratis (sin tarjeta) |
| Groq | https://console.groq.com/keys | Free tier con cuota diaria |
| OpenAI | https://platform.openai.com/api-keys | De pago |
| Anthropic | https://console.anthropic.com/settings/keys | De pago |
| xAI | https://console.x.ai/ | De pago |

> Para empezar sin costo: **Gemini 2.5 Flash** (sin tarjeta) o **Groq** (Llama 3.3 70B, muy rápido).

---

### 6. Configurar datos del candidato

```bash
cp data/candidate_data.example.json data/candidate_data.json
```

Editar `data/candidate_data.json` con los datos reales. Campos principales:

| Campo | Descripción |
|---|---|
| `personal_info` | Nombre, email, teléfono, LinkedIn, ubicación y GitHub (opcional) |
| `summary_base` | Párrafo base del candidato (el LLM lo adapta al JD) |
| `technical_skills` | Dict de categoría → lista de skills |
| `experience` | Historial completo con responsabilidades, logros y tecnologías |
| `education` | Instituciones, títulos, años |
| `languages` | Idiomas con nivel |

> Incluir la mayor cantidad de detalle posible en `experience.responsibilities` y `experience.achievements` — el LLM selecciona y adapta lo más relevante para cada JD.

---

### 7. Configurar roles

```bash
cp data/roles.example.json data/roles.json
```

Cada rol define el contexto que recibe el LLM para enfocar el CV. Campos relevantes: `display_name`, `focus_areas`, `prioritize_skills`, `bullet_style`, `experience_selection_criteria`.

Para agregar un nuevo rol: editar `data/roles.json` con la misma estructura que los existentes y recargar la página.

---

### 8. Copiar el template de CV por defecto

```bash
cp web/cv_templates/default.example.json web/cv_templates/default.json
```

> **Este paso es obligatorio.** Sin el archivo `default.json`, el selector de templates queda vacío, el estado interno del frontend nunca se inicializa y como resultado: el preview del CV aparece en blanco y los botones de descarga (PDF y DOCX) no hacen nada.

---

### 9. (Opcional) Agregar plantilla Word

Colocar `templates/cv_template.docx` con los macros `{{MACRO}}` correspondientes. También se puede subir desde la interfaz: **Settings → Word Template**.

Ver la lista completa de macros disponibles en [docs/arquitectura.md](arquitectura.md#macros-disponibles-para-la-plantilla-word).

---

### 10. Levantar la aplicación

**macOS / Linux:**
```bash
./run_web.sh
```

El script activa el entorno virtual, configura `DYLD_LIBRARY_PATH` para WeasyPrint en macOS y acepta dos flags opcionales:

| Flag | Descripción | Ejemplo |
|---|---|---|
| `--host <ip>` | Interfaz en la que escucha uvicorn (default: `127.0.0.1`) | `--host 0.0.0.0` |
| `--port <n>` | Puerto (default: `8000`) | `--port 8080` |

**Acceso solo desde localhost (default):**
```bash
./run_web.sh
```

**Acceso desde la red local o Tailscale:**
```bash
./run_web.sh --host 0.0.0.0
```

> Con `--host 0.0.0.0` el servidor escucha en todas las interfaces. Útil al conectarse vía Tailscale u otra red remota.

**Windows:**
```bash
.venv\Scripts\activate
uvicorn web.main:app --reload --port 8000
# Para acceso remoto: uvicorn web.main:app --reload --host 0.0.0.0 --port 8000
```

Abrir en el navegador: **http://localhost:8000** (o la IP/hostname de Tailscale si se usó `--host 0.0.0.0`)

---

## Opción B: Docker

La imagen incluye Python 3.10-slim con todas las librerías de sistema para WeasyPrint preinstaladas. Los datos personales, templates y output se montan como volúmenes para que persistan entre reinicios del contenedor.

### 1. Clonar el repositorio y preparar los archivos de datos

```bash
git clone <url-del-repo>
cd smart-cv-builder
cp .env.example .env                                                    # agregar API keys
cp data/candidate_data.example.json data/candidate_data.json
cp data/roles.example.json data/roles.json
cp web/cv_templates/default.example.json web/cv_templates/default.json
```

### 2. Levantar con Docker Compose

```bash
docker compose up
```

La app queda disponible en **http://localhost:8002** (el compose expone el puerto 8002 del host al 8000 del contenedor).

Para correr en segundo plano:
```bash
docker compose up -d
```

Para detener:
```bash
docker compose down
```

### Volúmenes montados

| Volumen local | Contenido |
|---|---|
| `./data` | `candidate_data.json` y `roles.json` |
| `./web/cv_templates` | Templates guardados desde la UI |
| `./output` | CVs generados (si se usa el CLI dentro del contenedor) |
| `./templates` | Plantilla Word para exportación DOCX |

> El archivo `.env` se lee via `env_file` en el compose. Las API keys nunca se copian dentro de la imagen.

---

## Verificar que funciona

1. Abrir `http://localhost:8000` (local) o `http://localhost:8002` (Docker) — debe aparecer la interfaz con 3 paneles
2. Activar **Dry run** en el panel izquierdo
3. Escribir cualquier texto en **Job Description** y hacer clic en **Generate CV**
4. El preview debe actualizarse con un CV de ejemplo sin llamar al LLM

---

## CLI (alternativa a la web)

```bash
python generate_cv.py --role backend_engineer --jd job_description.txt --provider groq
```

Los CVs generados se guardan en `output/`. El CLI produce DOCX y convierte a PDF usando LibreOffice en modo headless (debe estar instalado: `brew install --cask libreoffice` en macOS).
