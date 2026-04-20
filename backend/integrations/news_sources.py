from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

import feedparser
import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; NovaNorteBot/1.0; +https://novanorte.com.br)"
)
HTTP_TIMEOUT = 15.0
MAX_ITEMS_PER_SOURCE = 5


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    summary: str
    published_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def _in_last_hours(dt: datetime, hours: int) -> bool:
    now = datetime.now(timezone.utc)
    return (now - dt) <= timedelta(hours=hours)


def _parse_date(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def fetch_site(url: str, hours: int = 36) -> list[NewsItem]:
    """Baixa uma pagina e extrai titulos + links de artigos recentes."""
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
    except Exception as exc:
        log.warning("Falha ao baixar %s: %s", url, exc)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    items: list[NewsItem] = []

    for article in soup.find_all(["article", "li"], limit=40):
        heading = article.find(["h1", "h2", "h3"])
        link = article.find("a", href=True)
        if not heading or not link:
            continue
        title = heading.get_text(strip=True)
        href = link["href"]
        if not title or len(title) < 15:
            continue
        if href.startswith("/"):
            href = urllib.parse.urljoin(url, href)
        summary_tag = article.find("p")
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        items.append(
            NewsItem(
                title=title[:240],
                url=href,
                source=urllib.parse.urlparse(url).netloc,
                summary=summary[:400],
                published_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        if len(items) >= MAX_ITEMS_PER_SOURCE:
            break

    return items


def fetch_google_news(query: str, hours: int = 36) -> list[NewsItem]:
    """Usa RSS do Google News (gratis, sem auth)."""
    encoded = urllib.parse.quote(query)
    feed_url = (
        f"https://news.google.com/rss/search?q={encoded}"
        "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )
    parsed = feedparser.parse(feed_url)
    items: list[NewsItem] = []
    for entry in parsed.entries[:10]:
        published = _parse_date(getattr(entry, "published", None))
        if not _in_last_hours(published, hours):
            continue
        items.append(
            NewsItem(
                title=entry.title,
                url=entry.link,
                source=getattr(entry.source, "title", "Google News") if hasattr(entry, "source") else "Google News",
                summary=getattr(entry, "summary", "")[:400],
                published_at=published.isoformat(),
            )
        )
    return items


def fetch_instagram_profile(username: str, hours: int = 36) -> list[NewsItem]:
    """Pega posts publicos recentes. Lazy import porque instaloader eh pesado."""
    try:
        import instaloader
    except ImportError:
        log.warning("instaloader nao instalado, pulando IG")
        return []

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern="",
    )
    items: list[NewsItem] = []
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        for post in profile.get_posts():
            if not _in_last_hours(post.date_utc.replace(tzinfo=timezone.utc), hours):
                break
            items.append(
                NewsItem(
                    title=(post.caption or "").split("\n", 1)[0][:240] or f"Post de @{username}",
                    url=f"https://www.instagram.com/p/{post.shortcode}/",
                    source=f"instagram.com/{username}",
                    summary=(post.caption or "")[:400],
                    published_at=post.date_utc.replace(tzinfo=timezone.utc).isoformat(),
                )
            )
            if len(items) >= 3:
                break
    except Exception as exc:
        log.warning("Falha ao ler IG @%s: %s", username, exc)

    return items


def collect_all(
    urls: list[str],
    google_queries: list[str],
    ig_profiles: list[str],
    hours: int = 36,
) -> list[NewsItem]:
    items: list[NewsItem] = []
    for url in urls:
        items.extend(fetch_site(url, hours=hours))
    for q in google_queries:
        items.extend(fetch_google_news(q, hours=hours))
    for profile in ig_profiles:
        items.extend(fetch_instagram_profile(profile, hours=hours))

    seen: set[str] = set()
    deduped: list[NewsItem] = []
    for item in items:
        key = item.url
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    log.info("Coletadas %d noticias unicas", len(deduped))
    return deduped
