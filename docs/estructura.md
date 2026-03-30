# Estructura del proyecto

```
smart-cv-builder/
│
├── generate_cv.py              # CLI alternativo a la interfaz web
├── run_web.sh                  # Script para levantar la app (activa venv, configura DYLD_LIBRARY_PATH en macOS)
├── requirements.txt
├── .env.example                # Variables de entorno disponibles (copiar a .env)
├── CLAUDE.md                   # Instrucciones para Claude Code
│
├── data/                       # Datos del candidato y roles (gitignored, excepto .example)
│   ├── candidate_data.json         # Perfil del candidato (gitignored)
│   ├── candidate_data.example.json # Estructura de ejemplo para copiar
│   ├── roles.json                  # Definición de roles (gitignored)
│   └── roles.example.json          # Estructura de ejemplo para copiar
│
├── templates/
│   └── cv_template.docx        # Plantilla Word con macros {{MACRO}} (gitignored, opcional)
│
├── output/                     # CVs generados por CLI (gitignored)
│
├── config/
│   └── settings.py             # Singleton con todas las configuraciones y rutas. Lee .env.
│
├── schemas/                    # Modelos Pydantic compartidos (no web-specific)
│   ├── candidate.py            # CandidateData, PersonalInfo, Experience, Education, etc.
│   ├── llm_response.py         # LLMResponse, ExperienceLLM (estructura esperada del LLM)
│   └── roles.py                # RoleContext (campos que guían al LLM para cada perfil)
│
├── core/                       # Lógica de negocio independiente del framework web
│   ├── prompt_builder.py       # Construye system_prompt + user_prompt para el LLM
│   ├── response_parser.py      # Parsea y valida el JSON crudo del LLM (3 capas fallback)
│   └── word_injector.py        # Inyecta replacements en plantilla .docx (maneja fragmentación XML)
│
├── providers/                  # Adaptadores para cada proveedor LLM
│   ├── base.py                 # BaseProvider (ABC): interfaz generate(system, user) → str
│   ├── factory.py              # get_provider(name) → instancia concreta
│   ├── groq_provider.py
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   └── xai_provider.py
│
└── web/                        # Todo lo relacionado con la app FastAPI
    ├── main.py                 # Punto de entrada: registra routers, sirve estáticos, /api/roles
    ├── dependencies.py         # Dependencias inyectables de FastAPI
    │
    ├── routers/                # Un archivo por grupo de endpoints
    │   ├── generate.py         # POST /api/generate, /api/preview, /api/cover-letter
    │   ├── templates_router.py # CRUD GET/POST/PUT/DELETE /api/templates/{id}
    │   ├── export.py           # POST /api/export/pdf, /api/export/docx
    │   ├── ats.py              # POST /api/ats/score
    │   └── data_editor.py      # GET/PUT /api/candidate-data, /api/roles-data
    │                           # GET /api/docx-template/info, POST /api/docx-template
    │
    ├── services/               # Lógica de aplicación (orquestación y rendering)
    │   ├── cv_service.py       # Pipeline principal: carga datos → LLM → replacements
    │   ├── html_renderer.py    # render_cv_html(replacements, template) → HTML string
    │   ├── pdf_service.py      # html_to_pdf(html) → bytes (WeasyPrint)
    │   └── ats_service.py      # score_ats(...) → AtsScoreDetail
    │
    ├── schemas/                # Modelos Pydantic específicos de la API web
    │   ├── api_models.py       # GenerateRequest/Response, ExportRequest, CoverLetterRequest, etc.
    │   └── cv_template_schema.py # CvTemplate, CvTemplateSection, PageConfig
    │
    ├── storage/
    │   └── template_store.py   # Lee/escribe templates JSON en web/cv_templates/
    │
    ├── cv_templates/           # Templates guardados como JSON (gitignored excepto .example)
    │   ├── default.json            # Template por defecto (gitignored)
    │   └── default.example.json    # Ejemplo con todas las secciones disponibles
    │
    ├── html_themes/
    │   └── classic.html.j2     # Único tema HTML disponible. Jinja2 con estilos embebidos.
    │
    └── static/                 # Frontend servido directamente
        ├── index.html          # App shell con los 3 paneles y modal de settings
        ├── css/app.css
        └── js/
            ├── app.js          # Estado global, orquesta llamadas a /api/generate
            ├── editor.js       # Editor de template: drag & drop, config de página y secciones
            ├── preview.js      # Actualiza iframe con debounce (300ms) via /api/preview
            ├── ats.js          # Muestra keywords matched/missing del JD
            └── settings.js     # Modal de settings: candidate data, roles, DOCX template
```

---

## Separación de capas

| Capa | Responsabilidad | No debe contener |
|---|---|---|
| `core/` | Lógica de negocio pura (prompts, parsing, inyección Word) | Dependencias de FastAPI, referencias a rutas de archivos |
| `providers/` | Adaptadores LLM (1 archivo por proveedor) | Lógica de negocio, routing |
| `web/routers/` | Mapeo HTTP → service call, manejo de errores HTTP | Lógica de negocio |
| `web/services/` | Orquestación del pipeline, rendering | Routing HTTP |
| `schemas/` (raíz) | Modelos de datos del dominio | Modelos request/response web |
| `web/schemas/` | Modelos request/response de la API | Modelos del dominio |

---

## Archivos gitignoreados relevantes

| Archivo / carpeta | Razón |
|---|---|
| `data/candidate_data.json` | Datos personales del candidato |
| `data/roles.json` | Roles configurados |
| `templates/cv_template.docx` | Plantilla Word personalizada |
| `web/cv_templates/*.json` (excepto `*.example.json`) | Templates guardados desde la UI |
| `.env` | API keys |
| `output/` | CVs generados por CLI |

Cada uno tiene un archivo `.example.*` o equivalente en el repo que sirve como punto de partida.
