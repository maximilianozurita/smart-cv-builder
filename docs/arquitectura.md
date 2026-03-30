# Arquitectura

## Visión general

Smart CV Builder es una aplicación web FastAPI que orquesta un pipeline de generación de CVs usando LLMs. El flujo completo va desde el input del usuario (job description + rol) hasta la entrega de HTML renderizable, PDF y DOCX.

---

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Vanilla JS)               │
│  app.js · editor.js · preview.js · ats.js · settings.js │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP (REST JSON)
┌──────────────────▼──────────────────────────────────────┐
│                  FastAPI (web/main.py)                  │
│                                                         │
│  /api/generate     → routers/generate.py               │
│  /api/preview      → routers/generate.py               │
│  /api/cover-letter → routers/generate.py               │
│  /api/export/pdf   → routers/export.py                 │
│  /api/export/docx  → routers/export.py                 │
│  /api/ats/score    → routers/ats.py                    │
│  /api/templates/*  → routers/templates_router.py       │
│  /api/candidate-data · /api/roles-data → data_editor.py│
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Services (web/services/)                  │
│                                                         │
│  cv_service.py      ← orquesta el pipeline              │
│  html_renderer.py   ← Jinja2 → HTML                    │
│  pdf_service.py     ← WeasyPrint HTML → PDF bytes       │
│  ats_service.py     ← keyword matching sin deps        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                     Core (core/)                        │
│                                                         │
│  prompt_builder.py  ← construye system + user prompts   │
│  response_parser.py ← parsea JSON del LLM (3 capas)    │
│  word_injector.py   ← inyecta macros en .docx           │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Providers (providers/)                    │
│                                                         │
│  factory.py  →  GroqProvider / GeminiProvider /         │
│                 OpenAIProvider / AnthropicProvider /    │
│                 XAIProvider                             │
│  Todos implementan BaseProvider.generate(sys, usr)→str  │
└─────────────────────────────────────────────────────────┘
```

---

## Pipeline de generación (POST /api/generate)

```
GenerateRequest (job_description, role, provider, dry_run, template_id)
  │
  ├─ template_store.get_template(template_id)        # carga template JSON
  │
  └─ cv_service.run_pipeline()
       │
       ├─ _load_candidate()    → CandidateData (Pydantic)
       ├─ _load_role(role_key) → RoleContext (Pydantic)
       │
       ├─ prompt_builder.build_prompt(candidate, role, jd)
       │    ├─ system_prompt: reglas estrictas + OUTPUT_FORMAT JSON
       │    └─ user_prompt: JD + rol + skills + summary_base + experience history
       │
       ├─ [dry_run=False] provider.generate(system_prompt, user_prompt) → raw str
       │  [dry_run=True]  _mock_raw(candidate) → raw str hardcodeado
       │
       ├─ response_parser.parse_and_validate(raw) → LLMResponse (Pydantic)
       │    └─ 3 capas de fallback:
       │         1. strip markdown fences
       │         2. json.loads()
       │         3. regex extraction de {...}
       │         4. Pydantic validation → LLMResponse
       │
       └─ build_replacements(candidate, llm_obj)
            └─ merge: datos directos (personal_info, education, languages)
                    + output LLM (profile, skills, experiences)
            → dict {MACRO: valor}

  ├─ html_renderer.render_cv_html(replacements, template)
  │    └─ Jinja2 renderiza classic.html.j2
  │         con secciones visibles del template en el orden configurado
  │
  ├─ ats_service.score_ats(jd, profile, skills, bullets)
  │    └─ keyword extraction sin deps externas → matched/missing + score 0-100
  │
  └─ GenerateResponse { llm_response, replacements, preview_html, ats_score, cover_letter }
```

---

## Separación: qué toca el LLM y qué no

| Dato | Origen | Procesado por LLM |
|---|---|---|
| `personal_info` (nombre, email, teléfono, LinkedIn, ubicación) | `candidate_data.json` | No — inyección directa |
| `education` | `candidate_data.json` | No — inyección directa |
| `languages` | `candidate_data.json` | No — inyección directa |
| `certifications` | `candidate_data.json` | No — inyección directa |
| `profile` | LLM output | Sí — reescrito para el JD |
| `skills` | LLM output | Sí — reagrupado y priorizado |
| `experiences` (exactamente 2) | LLM output | Sí — selección + bullets adaptados |
| `cover_letter` | LLM output | Sí — generado completo |

---

## Providers LLM

Todos los providers implementan `BaseProvider.generate(system_prompt, user_prompt) -> str`. Los modelos son configurables vía `.env`:

| Provider | Variable de modelo | Default | Nota |
|---|---|---|---|
| Groq | `GROQ_MODEL` | `llama-3.3-70b-versatile` | Free tier |
| Gemini | `GEMINI_MODEL` | `gemini-2.5-flash` | Gratis |
| OpenAI | `OPENAI_MODEL` | `gpt-4o` | De pago |
| Anthropic | `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | De pago |
| xAI | `XAI_MODEL` | `grok-3-mini` | De pago |

> Anthropic usa el parámetro `system=` de su API por separado. Los demás providers incluyen el system prompt como primer mensaje en el array de mensajes.

---

## Modelo async

FastAPI es async. Las operaciones bloqueantes se despachan a un thread pool para no bloquear el event loop:

```python
raw = await loop.run_in_executor(None, _call_llm)   # LLM call
pdf = await loop.run_in_executor(None, html_to_pdf)  # WeasyPrint
```

Esto permite manejar requests concurrentes aunque cada generación tarde 10-30s.

---

## Schema de CvTemplate (Pydantic)

```
CvTemplate
├── id: str (UUID autogenerado)
├── name: str
├── theme: str = "classic"
├── output_filename: str = "cv"
├── page: PageConfig
│   ├── margin_top/bottom/left/right_mm: float
│   ├── font_family: str
│   ├── base_font_size_pt: float
│   ├── accent_color: str  ← bordes, bullets, títulos de sección
│   └── title_color: str   ← nombre del candidato (h1)
└── sections: List[CvTemplateSection]
    ├── id: str
    ├── type: str  (header|text_block|skills_block|experience_block|education_block)
    ├── order: int
    ├── visible: bool
    └── config: dict  (title, text_align, name_font_size según tipo)
```

Se persiste como JSON en `web/cv_templates/{id}.json`. El frontend re-renderiza el preview via `POST /api/preview` con debounce de 300ms cada vez que el template cambia.

---

## ATS Scoring

El scoring corre en proceso, sin dependencias externas (`ats_service.py`):

1. Tokeniza el job description extrayendo términos técnicos relevantes
2. Compara contra profile + skills + experience bullets del CV generado
3. Devuelve `score` (0-100), `matched_keywords`, `missing_keywords` y `section_scores` por sección

Se ejecuta automáticamente al final de cada `/api/generate` y también está disponible de forma independiente en `POST /api/ats/score`.

---

## Cover letter: pipeline principal vs. endpoint independiente

La cover letter se genera en la misma llamada LLM que el CV (campo `cover_letter` en el JSON de respuesta). Esto ahorra una llamada en el caso común.

`POST /api/cover-letter` existe para regenerar solo la carta sin re-ejecutar el pipeline. Usa un system prompt distinto: más enfocado en tono conversacional, sin el formato JSON estricto del pipeline principal.

---

## Templates de CV

Los templates se guardan como JSON en `web/cv_templates/`. Cada template define la apariencia visual completa del CV: fuente, tamaño, márgenes, colores y lista de secciones con su orden y visibilidad.

El template `default` siempre existe y no puede eliminarse. Los templates guardados desde la interfaz son personales y están en `.gitignore`.

---

## Inyección en plantilla Word

La descarga DOCX usa `templates/cv_template.docx` con macros `{{MACRO}}`. El inyector (`core/word_injector.py`) maneja dos tipos:

- **String** → reemplazo de texto en el lugar del macro (con consolidación de runs para manejar la fragmentación XML de Word)
- **List[str]** → el párrafo del macro se clona una vez por bullet y el original se elimina (usado para `{{EXPERIENCE_DESCRIPTION_N}}`)

---

## Macros disponibles para la plantilla Word

| Macro | Contenido |
|---|---|
| `{{FULL_NAME}}` | Nombre completo |
| `{{LOCATION}}` | Ubicación |
| `{{EMAIL}}` | Email |
| `{{PHONE}}` | Teléfono |
| `{{LINKEDIN}}` | URL de LinkedIn |
| `{{PROFILE}}` | Párrafo de perfil (LLM) |
| `{{SKILLS}}` | Skills en grupos (LLM) |
| `{{EXPERIENCE_COMPANY_1}}` / `{{EXPERIENCE_COMPANY_2}}` | Empresa |
| `{{EXPERIENCE_ROLE_1}}` / `{{EXPERIENCE_ROLE_2}}` | Cargo |
| `{{EXPERIENCE_START_DATE_1}}` / `{{EXPERIENCE_START_DATE_2}}` | Fecha inicio |
| `{{EXPERIENCE_END_DATE_1}}` / `{{EXPERIENCE_END_DATE_2}}` | Fecha fin |
| `{{EXPERIENCE_DESCRIPTION_1}}` / `{{EXPERIENCE_DESCRIPTION_2}}` | Bullets (lista) |
| `{{EDUCATION_INSTITUTION_1}}` / `{{EDUCATION_INSTITUTION_2}}` | Institución |
| `{{EDUCATION_DEGREE_1}}` / `{{EDUCATION_DEGREE_2}}` | Título |
| `{{EDUCATION_END_DATE_1}}` / `{{EDUCATION_END_DATE_2}}` | Año de graduación |
| `{{LANGUAGES}}` | Idiomas |
| `{{CERTIFICATIONS}}` | Certificaciones |

---

## Agregar un nuevo provider

1. Crear `providers/<nombre>_provider.py` subclaseando `BaseProvider`
2. Registrarlo en `providers/factory.py`
3. Agregar `<NOMBRE>_API_KEY` y `<NOMBRE>_MODEL` en `config/settings.py` y `.env.example`
4. Agregarlo al `<select>` de providers en `web/static/index.html`
