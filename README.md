# assistente-diario

Pipeline automatizado de carrosseis para redes sociais da **Nova Norte Distribuidora**
(oficial Grupo Heineken no Norte/Noroeste do ES).

Todo dia as 7h, uma cadeia de agentes Claude coleta noticias, escolhe as melhores,
gera copy e renderiza carrosseis de Instagram (4-7 laminas) que vao para o Google Drive.

## Status

| Fase | Escopo | Status |
|---|---|---|
| 1 | Scaffolding, `news_agent`, 1 template HTML/CSS, render Playwright | em andamento |
| 2 | `ideas_agent`, `copy_agent`, `design_agent`, 4 templates, upload Drive | pendente |
| 3 | Scheduler GitHub Actions, expansao para outras marcas | pendente |

## Setup local (Fase 1)

```bash
# 1. Python 3.11+
python -m venv .venv && source .venv/bin/activate

# 2. Dependencias
pip install -r requirements.txt
playwright install chromium

# 3. Config
cp .env.example .env
# edite .env e preencha ANTHROPIC_API_KEY

# 4. Logos
# coloque os PNGs em backend/design/assets/logos/
# (nomes esperados estao em backend/design/assets/logos/README.md)
```

## Comandos

```bash
# Coleta e ranqueia 5 noticias do dia
python -m backend.main news

# Renderiza 1 slide de teste (valida template + Playwright)
python -m backend.main demo-slide --title "CHEGOU FYS ZERO" --subtitle "O sabor sem acucares e calorias"

# Pipeline completo (Fase 2, ainda nao implementado)
python -m backend.main run
```

Saidas em `backend/output/YYYY-MM-DD/`.

## Estrutura

```
backend/
  agents/          news_agent, (ideas|copy|design)_agent na Fase 2
  integrations/    anthropic_client, news_sources (HTTP+RSS+IG), google_drive
  design/
    templates/     HTML/CSS on-brand (Jinja2)
    assets/        logos/ e fonts/
    renderer.py    Playwright -> PNG + PDF
  output/          gitignored; geracoes locais
  main.py          CLI
```

## Fontes de noticia

Configuradas em `.env`:
- **NEWS_URLS** — sites diretos (heinekenbrasil, exame, valor, brejas, cervesia, etc.)
- **GOOGLE_NEWS_QUERIES** — buscas no Google News RSS
- **IG_PROFILES** — perfis publicos monitorados via instaloader

## Proximos passos

Ver `/root/.claude/plans/perfeito-vamos-l-estou-delegated-porcupine.md`.
