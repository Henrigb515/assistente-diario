from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from backend.agents import news_agent
from backend.config import settings
from backend.design.renderer import build_pdf, render_slide


def _configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def cmd_news(_args: argparse.Namespace) -> None:
    result = news_agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_demo_slide(args: argparse.Namespace) -> None:
    today = date.today().isoformat()
    out_dir = settings.output_dir / today / "demo"
    png = render_slide(
        "hero_promo.html",
        {
            "eyebrow": "Nova Norte apresenta",
            "title": args.title or "Chegou o verao",
            "subtitle": args.subtitle or "3 combos Esquenta Verao para blindar seu estoque.",
            "body": "Preco de fabrica + brindes exclusivos para seu bar.",
            "cta": "Pedir no Heishop",
            "primary_color": "#0a7c3a",
            "accent_color": "#e8d12f",
            "distributor_logo": "nova_norte.png",
            "brand_logo": "heineken.png",
            "page_indicator": "01 / 01",
        },
        out_dir / "slide_01.png",
    )
    pdf = build_pdf([png], out_dir / "carrossel.pdf")
    print(f"PNG: {png}")
    if pdf:
        print(f"PDF: {pdf}")
    else:
        print("PDF: falhou (PNG gerado normalmente, segue para validacao visual)")


def cmd_run(_args: argparse.Namespace) -> None:
    raise SystemExit(
        "Pipeline completo ainda nao implementado (Fase 2). "
        "Use `python -m backend.main news` ou `demo-slide` por enquanto."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assistente-diario")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("news", help="Coleta e ranqueia as 5 melhores noticias").set_defaults(func=cmd_news)

    demo = sub.add_parser("demo-slide", help="Renderiza 1 slide de teste para validar template")
    demo.add_argument("--title", default=None)
    demo.add_argument("--subtitle", default=None)
    demo.set_defaults(func=cmd_demo_slide)

    sub.add_parser("run", help="Executa pipeline completo (Fase 2)").set_defaults(func=cmd_run)

    return parser


def main() -> None:
    _configure_logging()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
