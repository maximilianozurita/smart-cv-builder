# cvAutomat

CLI tool that uses an LLM to generate a tailored CV in Word (`.docx`) and PDF format, based on your candidate data and a job description.

## How it works

```
generate_cv.py (CLI)
  → loads your candidate data + role context + job description
  → sends relevant info to an LLM (skills, summary, experience)
  → LLM returns a tailored profile, skills and experience bullets
  → injects everything into a Word template via {{MACRO}} placeholders
  → saves .docx and optionally converts to PDF
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> Python 3.10+ recommended.

### 2. Configure API keys

Copy the example env file and fill in at least one provider key:

```bash
cp .env.example .env
```

Open `.env` and add your key. The fastest/cheapest option to start is **Groq** (free tier):

| Provider  | Get API key at                          |
|-----------|-----------------------------------------|
| Groq      | https://console.groq.com/keys          |
| OpenAI    | https://platform.openai.com/api-keys   |
| Anthropic | https://console.anthropic.com/settings/keys |
| xAI       | https://console.x.ai/                  |
| Gemini    | https://aistudio.google.com/app/apikey |

### 3. Add your candidate data

Copy the example and fill it in with your real information:

```bash
cp data/candidate_data.example.json data/candidate_data.json
```

Edit `data/candidate_data.json` with your data. The file has these sections:

| Section | What to fill |
|---|---|
| `personal_info` | Name, location, email, phone, LinkedIn URL |
| `languages` | Languages and proficiency levels |
| `education` | Institutions, degrees, graduation years |
| `summary_base` | A short paragraph about yourself (used as base for the LLM) |
| `technical_skills` | Skills grouped by category (programming, tools, databases, etc.) |
| `experience` | Work history with responsibilities and achievements (see below) |
| `certifications` | Optional certifications with issuer and credential URL |
| `soft_skills` | Optional list of soft skills |

#### Experience entries

Each entry in `experience` needs:
- `id`: unique identifier, e.g. `"exp1"`
- `company`, `role`, `start_date`, `end_date`
- `description`: one-line summary of what the role was about
- `responsibilities`: full list of things you did (the LLM picks the most relevant ones)
- `technologies`: list of tools/languages used
- `achievements`: list of concrete accomplishments

> The LLM selects and rewrites content from `responsibilities` and `achievements` based on the job description. Add as much detail as possible — more context = better output.

### 4. Add your Word template

Place your CV template at `templates/cv_template.docx`.

The template must use `{{MACRO}}` placeholders where you want content injected. Available macros:

| Macro | Content |
|---|---|
| `{{FULL_NAME}}` | Full name |
| `{{LOCATION}}` | Location |
| `{{EMAIL}}` | Email |
| `{{PHONE}}` | Phone |
| `{{LINKEDIN}}` | LinkedIn URL |
| `{{PROFILE}}` | LLM-generated profile summary |
| `{{SKILLS}}` | LLM-formatted technical skills |
| `{{EXPERIENCE_COMPANY_1}}` | Company name (experience 1) |
| `{{EXPERIENCE_ROLE_1}}` | Role title (experience 1) |
| `{{EXPERIENCE_START_DATE_1}}` | Start date (experience 1) |
| `{{EXPERIENCE_END_DATE_1}}` | End date (experience 1) |
| `{{EXPERIENCE_DESCRIPTION_1}}` | Bullet list of responsibilities (experience 1) |
| `{{EXPERIENCE_COMPANY_2}}` | Company name (experience 2) |
| `{{EXPERIENCE_ROLE_2}}` | Role title (experience 2) |
| `{{EXPERIENCE_START_DATE_2}}` | Start date (experience 2) |
| `{{EXPERIENCE_END_DATE_2}}` | End date (experience 2) |
| `{{EXPERIENCE_DESCRIPTION_2}}` | Bullet list of responsibilities (experience 2) |
| `{{EDUCATION_INSTITUTION_1}}` — `{{EDUCATION_INSTITUTION_2}}` | Institution name |
| `{{EDUCATION_DEGREE_1}}` — `{{EDUCATION_DEGREE_2}}` | Degree title |
| `{{EDUCATION_END_DATE_1}}` — `{{EDUCATION_END_DATE_2}}` | Graduation year |
| `{{LANGUAGES}}` | Languages string |
| `{{CERTIFICATIONS}}` | Certifications string |

> `{{EXPERIENCE_DESCRIPTION_N}}` placeholders are replaced with a bullet list — one paragraph per bullet. All other placeholders are simple text replacements.

### 5. (Optional) Add a job description

Paste the job description text into `job_description.txt`. The LLM uses it to tailor the content. If the file is empty, it generates a generic CV.

### 6. (Optional) PDF conversion

To enable automatic PDF generation after the `.docx` is created, install LibreOffice:

```bash
brew install --cask libreoffice
```

If LibreOffice is not installed, the tool will generate the `.docx` and print a warning.

---

## Usage

```bash
# Basic usage
python generate_cv.py --role backend_engineer --jd job_description.txt --provider groq

# Test the full pipeline without making an LLM call
python generate_cv.py --role backend_engineer --jd job_description.txt --provider groq --dry-run

# Specify custom template or output path
python generate_cv.py --role data_engineer --jd job.txt --provider openai \
  --template templates/my_template.docx --output output/my_cv.docx
```

### Arguments

| Argument | Description | Required |
|---|---|---|
| `--role` | Role context to use (see below) | Yes |
| `--jd` | Path to job description `.txt` file | Yes |
| `--provider` | LLM provider to use | Yes |
| `--template` | Path to Word template (default: `templates/cv_template.docx`) | No |
| `--output` | Path for output `.docx` (default: `output/<name>.docx`) | No |
| `--dry-run` | Run without calling the LLM (uses mock response) | No |

### Available roles

Roles define the context sent to the LLM. Defined in `data/roles.json`, you can add, delete, or update them according to your requirements:

- `backend_engineer`
- `data_engineer`
- `fullstack_engineer`
- `data_analyst`
- `software_engineer`
- `ia_developer`
- `automatization_developer`

### Available providers

- `groq` — Llama 3.3 70B (fast, free tier)
- `openai` — GPT-4o
- `anthropic` — Claude Sonnet
- `xai` — Grok 3 Mini
- `gemini` — Gemini 2.5 Flash

---

## Adding a new role

Edit `data/roles.json` and add a new entry following the existing structure.

## Adding a new provider

1. Create `providers/<name>_provider.py` subclassing `BaseProvider`
2. Register it in `providers/factory.py`
3. Add `<NAME>_API_KEY` and `<NAME>_MODEL` to `config/settings.py` and `.env.example`
4. Add the choice to `--provider` in `generate_cv.py`

---

## Project structure

```
cvAutomat/
├── generate_cv.py              # CLI entrypoint
├── requirements.txt
├── .env.example                # Copy to .env and fill API keys
├── data/
│   ├── candidate_data.json     # Your personal data (gitignored)
│   ├── candidate_data.example.json  # Template to copy from
│   └── roles.json              # Role definitions
├── templates/
│   └── cv_template.docx        # Your Word template (gitignored)
├── output/                     # Generated CVs land here (gitignored)
├── config/
│   └── settings.py             # Loads .env, model defaults
├── providers/                  # LLM provider implementations
├── core/
│   ├── prompt_builder.py       # Builds system + user prompt
│   ├── response_parser.py      # Parses and validates LLM output
│   └── word_injector.py        # Injects content into Word template
└── schemas/                    # Pydantic models
```
