# Smart CV Builder

Herramienta con interfaz web para generar CVs en PDF y Word (.docx) adaptados a una oferta laboral específica, usando LLMs para redactar el perfil, habilidades y bullets de experiencia.

## Documentación

| | |
|---|---|
| [⚙️ Arquitectura](docs/arquitectura.md) | Pipeline de generación, componentes, providers y templates |
| [📁 Estructura](docs/estructura.md) | Árbol del proyecto, separación de capas y archivos gitignoreados |
| [🚀 Instalación](docs/instalacion.md) | Requisitos y pasos completos para correr el proyecto |
| [🔌 API](docs/api.md) | Endpoints, request/response y ejemplos |
| [🧠 Decisiones técnicas](docs/decisiones.md) | Trade-offs y justificaciones de diseño |

---

## Descripción

Dado un job description y un perfil de rol, el LLM reescribe el perfil del candidato, agrupa sus skills y selecciona exactamente 2 experiencias con bullets adaptados al puesto. Los datos personales, educación e idiomas se inyectan directamente sin pasar por el LLM.

El resultado se entrega como HTML interactivo (preview editable), PDF descargable y DOCX via plantilla con macros.

---

## Uso rápido

```bash
# Levantar la app
./run_web.sh
# Abrir http://localhost:8000
```

1. Pegar el job description en el panel izquierdo
2. Seleccionar rol y proveedor LLM
3. Hacer clic en **✨ Generate CV**
4. Ajustar el template en el panel central (fuente, colores, secciones)
5. Descargar PDF o DOCX

Para probar sin API key: activar **Dry run** antes de generar.

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend / API | FastAPI + Uvicorn |
| Generación de PDF | WeasyPrint (HTML → PDF) |
| Templates HTML | Jinja2 (`.html.j2`) |
| Generación de DOCX | python-docx (inyección de macros) |
| Validación de datos | Pydantic v2 |
| Frontend | Vanilla JS (ES modules), sin frameworks |
| LLM providers | Groq, Gemini, OpenAI, Anthropic, xAI |

---

## Instalación rápida

```bash
git clone <url-del-repo> && cd smart-cv-builder
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # agregar al menos una API key
cp data/candidate_data.example.json data/candidate_data.json
cp data/roles.example.json data/roles.json
./run_web.sh
```

Para los requisitos del sistema (WeasyPrint), configuración de API keys y pasos detallados: ver [docs/instalacion.md](docs/instalacion.md).

---

## Arquitectura (resumen)

El pipeline central corre en `web/services/cv_service.py`: carga los datos del candidato, construye los prompts, llama al LLM, parsea el JSON de respuesta con 3 capas de fallback y arma los replacements. Luego `html_renderer.py` renderiza el CV con Jinja2 y `ats_service.py` calcula el keyword match contra el JD.

Ver el diagrama completo y detalle de cada componente en [docs/arquitectura.md](docs/arquitectura.md).

---

## Estructura del proyecto

```
smart-cv-builder/
├── core/          # Lógica de negocio: prompts, parser LLM, inyector Word
├── providers/     # Adaptadores LLM (Groq, Gemini, OpenAI, Anthropic, xAI)
├── schemas/       # Modelos Pydantic del dominio
├── web/
│   ├── routers/   # Endpoints FastAPI
│   ├── services/  # Pipeline, rendering, PDF, ATS
│   ├── schemas/   # Modelos request/response de la API
│   └── static/    # Frontend Vanilla JS
├── data/          # candidate_data.json + roles.json (gitignored)
└── templates/     # cv_template.docx (gitignored, opcional)
```

Árbol completo con anotaciones en [docs/estructura.md](docs/estructura.md).

---