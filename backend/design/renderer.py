from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright
from PIL import Image

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
ASSETS_DIR = Path(__file__).parent / "assets"

SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


def _asset_uri(path: Path) -> str:
    return path.resolve().as_uri()


def _resolve_logos(ctx: dict) -> dict:
    ctx = dict(ctx)
    for key in ("distributor_logo", "brand_logo"):
        value = ctx.get(key)
        if value and not value.startswith(("http://", "https://", "file://")):
            candidate = (ASSETS_DIR / "logos" / value).resolve()
            if candidate.exists():
                ctx[key] = _asset_uri(candidate)
            else:
                log.warning("Logo nao encontrada: %s", candidate)
                ctx[key] = ""
    return ctx


def render_slide(template_name: str, context: dict, out_png: Path) -> Path:
    template = _env.get_template(template_name)
    html = template.render(**_resolve_logos(context))
    out_png.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT},
            device_scale_factor=2,
        )
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=str(out_png), full_page=False, omit_background=False)
        browser.close()

    log.info("Render: %s", out_png)
    return out_png


def build_pdf(png_paths: list[Path], out_pdf: Path) -> Path:
    if not png_paths:
        raise ValueError("Lista de PNGs vazia")
    images = [Image.open(p).convert("RGB") for p in png_paths]
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        out_pdf,
        save_all=True,
        append_images=images[1:],
        resolution=150.0,
    )
    log.info("PDF gerado: %s", out_pdf)
    return out_pdf
