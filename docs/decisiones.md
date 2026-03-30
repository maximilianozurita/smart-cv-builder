# Decisiones técnicas

---

## FastAPI + Uvicorn como backend

**Decisión:** FastAPI sobre Flask, Django u otros.

**Por qué:** la generación de CV implica llamadas a LLMs que pueden tardar 10-30 segundos. FastAPI es async-native, lo que permite manejar múltiples requests concurrentes sin bloquear. Las llamadas bloqueantes (LLM, WeasyPrint, I/O de archivos) se despachan a un thread pool via `run_in_executor`. Flask no tiene soporte async nativo; Django es excesivo para este scope.

---

## Vanilla JS sin framework en el frontend

**Decisión:** ES modules puros, sin React/Vue/Svelte.

**Por qué:** la app tiene 3 paneles con interacciones bien definidas (generate → preview → export). Introducir un framework de componentes agrega build tooling (Vite/webpack), dependency management y complejidad de estado que no se justifica. El resultado es un frontend que no requiere `npm install` y funciona con `StaticFiles` de FastAPI directamente.

**Trade-off:** sin reactividad declarativa. El estado se maneja manualmente en `app.js`. Escala razonablemente para una app de single-user.

---

## WeasyPrint para generación de PDF

**Decisión:** WeasyPrint (HTML → PDF) sobre alternativas como Puppeteer, reportlab o PDFKit.

**Por qué:** el CV ya se renderiza como HTML con Jinja2 y estilos CSS embebidos. WeasyPrint convierte ese mismo HTML en PDF sin necesidad de un proceso headless de browser (Puppeteer requiere Chromium). El output es "lo que ves en el preview es lo que se descarga", sin discrepancias.

**Trade-off:** WeasyPrint requiere librerías nativas del sistema (Pango, Cairo, GDK-Pixbuf), lo que complica la instalación en algunos entornos. La documentación del README cubre todos los casos (macOS, Ubuntu, Fedora, Windows).

---

## Pydantic v2 para validación de datos

**Decisión:** Pydantic en todo el stack (schemas de candidato, LLM response, API models, templates).

**Por qué:** integración nativa con FastAPI. La validación estricta del output del LLM (`LLMResponse`) es crítica — si el LLM devuelve un JSON malformado o con campos faltantes, Pydantic lo detecta antes de que llegue al rendering. Esto complementa el sistema de fallback de 3 capas en `response_parser.py`.

---

## Fallback en 3 capas para parsear el LLM

**Decisión:** `response_parser.py` intenta parsear el output del LLM en 3 pasos antes de lanzar `ParseError`.

**Por qué:** los LLMs frecuentemente devuelven el JSON envuelto en markdown fences (```json ... ```), con texto extra antes o después, o con comillas mal escapadas. Sin este fallback, un 30-40% de las respuestas fallarían en producción dependiendo del proveedor.

Las capas son:
1. Strip de markdown fences
2. `json.loads()` directo
3. Regex extraction del primer `{...}` encontrado

---

## Templates como JSON en filesystem

**Decisión:** los templates se almacenan como archivos JSON en `web/cv_templates/` en lugar de una base de datos.

**Por qué:** la app está diseñada para uso personal (single-user). Una base de datos (SQLite, Postgres) agrega complejidad operacional innecesaria. Los archivos JSON son editables manualmente, hacen backup trivial, y se pueden compartir copiando un archivo. El `template_store.py` encapsula completamente el acceso.

**Trade-off:** no escala a multi-usuario. Aceptable para el caso de uso actual.

---

## Multi-provider con interfaz abstracta

**Decisión:** `BaseProvider` con `generate(system_prompt, user_prompt) → str` como único método requerido.

**Por qué:** los providers LLM tienen APIs radicalmente distintas (OpenAI y Groq usan mensajes array, Anthropic usa el parámetro `system=` separado, Gemini tiene su propio SDK). La abstracción permite cambiar de proveedor desde la UI sin modificar el pipeline. Agregar un nuevo provider requiere un solo archivo nuevo + registro en `factory.py`.

**Excepción documentada:** Anthropic pasa el system prompt via el parámetro dedicado `system=` de su API, a diferencia de los demás que lo incluyen como primer mensaje en el array.

---

## Sin framework de testing

**Decisión:** no hay tests automatizados.

**Por qué:** el pipeline de generación tiene una dependencia externa no determinista (el LLM). Mockear el LLM requeriría fixtures complejos que no garantizan representatividad. La UI incluye **Dry run** como mecanismo de test funcional integrado: ejecuta el pipeline completo con una respuesta hardcodeada, permitiendo verificar el rendering, el template y los exports sin gastar tokens.

**Consecuencia:** los cambios en `html_renderer.py` o `classic.html.j2` se verifican visualmente via dry run.

---

## Jinja2 con HTML y CSS embebido

**Decisión:** un único tema (`classic.html.j2`) con todos los estilos inline/embebidos.

**Por qué:** WeasyPrint maneja mejor CSS embebido que stylesheets externos al generar PDF. Mantener un solo archivo `.html.j2` simplifica el desarrollo del tema — todos los estilos, lógica de renderizado y variables del template están en un lugar. La parametrización se hace via las variables del `CvTemplate` (fuente, colores, márgenes) que se pasan al contexto Jinja2.

**Trade-off:** el archivo puede crecer. Si se agregan temas, se replicaría código CSS. Aceptable mientras hay un único tema.

---

## Cover letter en el mismo pipeline

**Decisión:** la cover letter se genera en la misma llamada al LLM que el CV, como campo `cover_letter` en el JSON de respuesta.

**Por qué:** ahorra una llamada al LLM en el caso más común. El endpoint `/api/cover-letter` existe para regeneración independiente cuando el usuario quiere ajustar el tono sin re-generar el CV completo.
