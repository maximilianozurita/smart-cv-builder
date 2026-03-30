# API Reference

Base URL: `http://localhost:8000`

---

## POST /api/generate

Ejecuta el pipeline completo: carga datos del candidato → llama al LLM → renderiza HTML → calcula ATS score.

**Request:**
```json
{
  "job_description": "string",
  "role": "backend_engineer",
  "provider": "gemini",
  "dry_run": false,
  "template_id": "default"
}
```

| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `job_description` | string | requerido | Texto completo de la oferta laboral |
| `role` | string | requerido | Key del rol en `data/roles.json` |
| `provider` | string | `"groq"` | `groq`, `gemini`, `openai`, `anthropic`, `xai` |
| `dry_run` | bool | `false` | Si `true`, usa respuesta mock sin llamar al LLM |
| `template_id` | string | `"default"` | ID del template de CV a usar |

**Response:**
```json
{
  "llm_response": {
    "profile": "...",
    "skills": "Group1: skill1, skill2 | Group2: skill1",
    "experiences": [...],
    "cover_letter": "..."
  },
  "replacements": { "FULL_NAME": "...", "PROFILE": "...", ... },
  "preview_html": "<html>...</html>",
  "ats_score": {
    "score": 78.5,
    "matched_keywords": ["python", "fastapi", ...],
    "missing_keywords": ["kubernetes", ...],
    "section_scores": { "profile": 80.0, "skills": 90.0, "experience": 70.0 }
  },
  "cover_letter": "..."
}
```

**Errores:**
- `400` — rol o proveedor inválido
- `422` — el LLM devolvió una respuesta que no pudo parsearse
- `500` — error del proveedor LLM u otro error interno

---

## POST /api/preview

Re-renderiza el HTML del CV con replacements y template ya calculados, sin llamar al LLM. Lo usa el frontend para actualizar el preview en tiempo real.

**Request:**
```json
{
  "replacements": { "FULL_NAME": "...", ... },
  "template": { "id": "...", "name": "...", "page": {...}, "sections": [...] }
}
```

**Response:**
```json
{ "preview_html": "<html>...</html>" }
```

---

## POST /api/cover-letter

Genera (o regenera) solo la cover letter sin re-ejecutar el pipeline completo.

**Request:**
```json
{
  "job_description": "string",
  "role": "backend_engineer",
  "provider": "gemini"
}
```

**Response:**
```json
{ "cover_letter": "Texto de la carta de presentación..." }
```

---

## POST /api/export/pdf

Genera y descarga el CV en PDF (WeasyPrint). Lo que se renderiza en el preview es lo que se descarga.

**Request:** igual que `/api/preview` (`replacements` + `template`)

**Response:** `application/pdf` — archivo binario con `Content-Disposition: attachment; filename=cv.pdf`

---

## POST /api/export/docx

Genera y descarga el CV en DOCX usando `templates/cv_template.docx` con los macros `{{MACRO}}`.

**Request:** igual que `/api/preview` (`replacements` + `template`)

**Response:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

**Error `404`** si `templates/cv_template.docx` no existe.

---

## POST /api/ats/score

Calcula el ATS score de forma independiente (sin generar el CV completo).

**Request:**
```json
{
  "job_description": "string",
  "profile": "string",
  "skills": "string",
  "experience_bullets": ["bullet 1", "bullet 2", ...]
}
```

**Response:** igual que el campo `ats_score` en `/api/generate`.

---

## GET /api/roles

Lista los roles disponibles en `data/roles.json`.

**Response:**
```json
[
  { "key": "backend_engineer", "label": "Backend Engineer" },
  { "key": "data_scientist", "label": "Data Scientist" }
]
```

---

## Templates CRUD

### GET /api/templates
Lista todos los templates disponibles.

### GET /api/templates/{template_id}
Devuelve un template específico. `404` si no existe.

### POST /api/templates
Crea un nuevo template. Body: objeto `CvTemplate` completo.

### PUT /api/templates/{template_id}
Actualiza un template existente. El `id` del body se sobreescribe con el de la URL.

### DELETE /api/templates/{template_id}
Elimina un template. `404` si no existe.

---

## Datos del candidato y roles

### GET /api/candidate-data
Devuelve el contenido de `data/candidate_data.json`.

### PUT /api/candidate-data
Sobreescribe `data/candidate_data.json` con el body JSON recibido.

### GET /api/roles-data
Devuelve el contenido de `data/roles.json`.

### PUT /api/roles-data
Sobreescribe `data/roles.json` con el body JSON recibido.

### GET /api/docx-template/info
Devuelve información sobre el archivo `templates/cv_template.docx`:
```json
{ "exists": true, "name": "cv_template.docx", "size_kb": 42.3 }
```

### POST /api/docx-template
Sube y reemplaza `templates/cv_template.docx`. Body: `multipart/form-data` con campo `file` (solo acepta `.docx`).

---

## Notas

- Todos los endpoints JSON usan `Content-Type: application/json`
- No hay autenticación — la app está diseñada para uso local
- La documentación interactiva (Swagger UI) está disponible en `/docs` al levantar la app con `uvicorn`
