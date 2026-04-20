from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from backend.config import settings
from backend.integrations.anthropic_client import chat_json
from backend.integrations.news_sources import NewsItem, collect_all

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Voce e um editor-chefe de conteudo digital para uma distribuidora oficial
do Grupo Heineken (Nova Norte, Norte/Noroeste do ES). Seu publico sao donos de bares,
restaurantes, mercados e consumidores finais.

Priorize noticias sobre:
- Lancamentos de produtos do portfolio Heineken (Heineken, Amstel, Eisenbahn, FYS, Sol,
  Kaiser, Tiger, Blue Moon, Baden Baden, Praya, Glacial, Itubaina)
- Mudancas fiscais ou regulatorias que impactam distribuidores (especialmente imposto seletivo)
- Tendencias de consumo de bebidas no Brasil
- Dados de mercado (participacao, crescimento, sell-out)
- Movimentos estrategicos do Grupo Heineken
- Oportunidades sazonais (datas comemorativas, eventos, clima)

IGNORE:
- Noticias sobre Devassa ou concorrentes nao autorizados
- Noticias internacionais sem impacto direto no Brasil
- Conteudo generico de economia sem relacao com bebidas"""

USER_TEMPLATE = """Abaixo estao {n} noticias coletadas nas ultimas 36 horas.
Selecione as 5 MAIS relevantes para gerar conteudo de Instagram para bares e restaurantes.

Para cada uma, retorne um objeto JSON no formato:
{{
  "title": "...",
  "url": "...",
  "source": "...",
  "summary": "resumo em 2-3 frases com o gancho para conteudo",
  "relevance_score": 1-10,
  "angle": "qual o angulo/gancho para uma distribuidora usar isso"
}}

Retorne SOMENTE um array JSON com os 5 itens escolhidos.

NOTICIAS:
{items_json}"""


def _latest_path(kind: str) -> Path:
    folder = settings.output_dir / kind
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{date.today().isoformat()}.json"


def run() -> list[dict]:
    settings.ensure_ready()

    raw_items: list[NewsItem] = collect_all(
        urls=settings.news_urls,
        google_queries=settings.google_news_queries,
        ig_profiles=settings.ig_profiles,
        hours=36,
    )

    if not raw_items:
        log.warning("Nenhuma noticia coletada; encerrando news_agent")
        return []

    raw_dump = [item.to_dict() for item in raw_items]
    user_prompt = USER_TEMPLATE.format(
        n=len(raw_dump),
        items_json=json.dumps(raw_dump, ensure_ascii=False, indent=2),
    )

    selected = chat_json(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=3000,
        temperature=0.3,
    )

    if not isinstance(selected, list):
        raise ValueError(f"Esperado array, recebi {type(selected)}")

    out_path = _latest_path("news")
    out_path.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("Salvou %d noticias selecionadas em %s", len(selected), out_path)
    return selected


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
