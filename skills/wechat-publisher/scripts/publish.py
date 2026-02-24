#!/usr/bin/env python3
"""
Publish a Markdown file to WeChat Official Account draft box.

Usage:
    python3 publish.py <markdown_file> [options]

Options:
    --cover PATH_OR_URL   Cover image (local path or https URL)
    --author NAME         Article author
    --digest TEXT         Article summary (auto-generated if omitted)
    --dry-run             Convert to HTML and save locally, without publishing

Config (searched in order):
    .wechat-publisher/.env   (project-level)
    ~/.wechat-publisher/.env (user-level)

.env format:
    WECHAT_APP_ID=wxxxxxxxxxxxxxxxxxxx
    WECHAT_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Requirements:
    pip install markdown requests Pygments beautifulsoup4
"""

import argparse
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

try:
    import markdown
    import requests
    from bs4 import BeautifulSoup
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer
    from pygments.util import ClassNotFound
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install markdown requests Pygments beautifulsoup4")
    sys.exit(1)


# ── Config ────────────────────────────────────────────────────────────────────

def load_env_file(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_config() -> tuple[str, str]:
    """Load WECHAT_APP_ID and WECHAT_APP_SECRET from env vars or .env files."""
    candidates = [
        Path(".wechat-publisher/.env"),
        Path.home() / ".wechat-publisher" / ".env",
    ]
    env = {}
    for path in candidates:
        env = load_env_file(path)
        if env:
            break

    app_id = os.environ.get("WECHAT_APP_ID") or env.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET") or env.get("WECHAT_APP_SECRET", "")

    if not app_id or not app_secret:
        print("Error: Missing WECHAT_APP_ID or WECHAT_APP_SECRET.")
        print("Create .wechat-publisher/.env with:")
        print("  WECHAT_APP_ID=wxxxxxxxxxxxxxxxxxxx")
        print("  WECHAT_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)

    return app_id, app_secret


# ── WeChat API ────────────────────────────────────────────────────────────────

API_BASE = "https://api.weixin.qq.com"


def get_access_token(app_id: str, app_secret: str) -> str:
    url = f"{API_BASE}/cgi-bin/token"
    resp = requests.get(url, params={
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret,
    }, timeout=15)
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"get_access_token failed: {data}")
    return data["access_token"]


def upload_image_for_content(image_source: str, token: str, base_dir: Path) -> str:
    """Upload image to WeChat permanent media, return CDN URL for use in article body."""
    image_bytes, content_type = _fetch_image(image_source, base_dir)
    ext = _ext_from_content_type(content_type)
    resp = requests.post(
        f"{API_BASE}/cgi-bin/material/add_material",
        params={"access_token": token, "type": "image"},
        files={"media": (f"image.{ext}", io.BytesIO(image_bytes), content_type)},
        timeout=30,
    )
    data = resp.json()
    if "url" not in data:
        raise RuntimeError(f"Image upload failed: {data}")
    return data["url"]


def upload_thumb(image_source: str, token: str, base_dir: Path) -> str:
    """Upload cover image, return thumb_media_id (required by draft/add API)."""
    image_bytes, content_type = _fetch_image(image_source, base_dir)
    # WeChat thumb only accepts jpg/png, not gif/webp
    if "gif" in content_type or "webp" in content_type:
        content_type = "image/jpeg"
    ext = _ext_from_content_type(content_type)
    resp = requests.post(
        f"{API_BASE}/cgi-bin/material/add_material",
        params={"access_token": token, "type": "thumb"},
        files={"media": (f"thumb.{ext}", io.BytesIO(image_bytes), content_type)},
        timeout=30,
    )
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"Thumb upload failed: {data}")
    return data["media_id"]


def add_draft(article: dict, token: str) -> str:
    """Create draft, return media_id."""
    resp = requests.post(
        f"{API_BASE}/cgi-bin/draft/add",
        params={"access_token": token},
        json={"articles": [article]},
        timeout=30,
    )
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"draft/add failed: {data}")
    return data["media_id"]


def _fetch_image(source: str, base_dir: Path) -> tuple[bytes, str]:
    """Fetch image bytes and content-type from URL or local path."""
    if source.startswith("http://") or source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=15) as r:
            return r.read(), r.headers.get("Content-Type", "image/jpeg").split(";")[0]
    else:
        local = Path(source) if Path(source).is_absolute() else base_dir / source
        if not local.exists():
            raise FileNotFoundError(f"Image not found: {local}")
        suffix = local.suffix.lower().lstrip(".")
        ct_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                  "gif": "image/gif", "webp": "image/webp"}
        return local.read_bytes(), ct_map.get(suffix, "image/jpeg")


def _ext_from_content_type(ct: str) -> str:
    return {"image/jpeg": "jpg", "image/png": "png",
            "image/gif": "gif", "image/webp": "jpg"}.get(ct, "jpg")


# ── Markdown → WeChat HTML ────────────────────────────────────────────────────

# WeChat strips <style> tags, so all styles must be inline.
STYLES = {
    "h1": "font-size:22px;font-weight:bold;margin:24px 0 12px;color:#1a1a1a;line-height:1.4;",
    "h2": "font-size:18px;font-weight:bold;margin:20px 0 10px;color:#1a1a1a;border-bottom:2px solid #07c160;padding-bottom:6px;",
    "h3": "font-size:16px;font-weight:bold;margin:16px 0 8px;color:#333;",
    "p":  "font-size:15px;line-height:1.9;margin:10px 0;color:#333;",
    "code_inline": "background:#f5f5f5;padding:2px 6px;border-radius:3px;font-family:'Courier New',monospace;font-size:13px;color:#c7254e;",
    "pre": "background:#1e1e1e;padding:16px;border-radius:6px;overflow-x:auto;margin:14px 0;",
    "blockquote": "border-left:4px solid #07c160;padding:8px 16px;background:#f6fffa;margin:12px 0;color:#555;",
    "img": "max-width:100%;height:auto;display:block;margin:12px auto;border-radius:4px;",
    "a": "color:#07c160;text-decoration:none;",
    "ul": "padding-left:22px;margin:10px 0;",
    "ol": "padding-left:22px;margin:10px 0;",
    "li": "font-size:15px;line-height:1.9;color:#333;margin:4px 0;",
    "table": "border-collapse:collapse;width:100%;margin:14px 0;font-size:14px;",
    "th": "background:#f0f0f0;border:1px solid #ddd;padding:8px 12px;text-align:left;font-weight:bold;",
    "td": "border:1px solid #ddd;padding:8px 12px;",
    "hr": "border:none;border-top:1px solid #e8e8e8;margin:20px 0;",
}


def _highlight_code(code: str, lang: str) -> str:
    """Syntax-highlight code block with inline styles via Pygments."""
    try:
        lexer = get_lexer_by_name(lang, stripall=True) if lang else guess_lexer(code)
    except ClassNotFound:
        lexer = TextLexer()
    formatter = HtmlFormatter(style="monokai", noclasses=True, nowrap=True)
    highlighted = highlight(code, lexer, formatter)
    return (
        f'<pre style="{STYLES["pre"]}">'
        f'<code style="font-family:\'Courier New\',monospace;font-size:13px;line-height:1.6;">'
        f'{highlighted}</code></pre>'
    )


def md_to_wechat_html(md_text: str) -> tuple[str, list[str]]:
    """
    Convert Markdown to WeChat-compatible HTML with inline styles.
    Returns (html, list_of_image_sources).
    """
    md_engine = markdown.Markdown(extensions=["extra", "sane_lists", "nl2br"])
    raw_html = md_engine.convert(md_text)
    soup = BeautifulSoup(raw_html, "html.parser")
    image_sources: list[str] = []

    for tag in soup.find_all(True):
        name = tag.name

        if name in ("h1", "h2", "h3"):
            tag["style"] = STYLES[name]

        elif name in ("h4", "h5", "h6"):
            tag["style"] = STYLES["h3"]

        elif name == "p":
            imgs = tag.find_all("img")
            if imgs and len(list(tag.children)) == len(imgs):
                tag.unwrap()
            else:
                tag["style"] = STYLES["p"]

        elif name == "img":
            src = tag.get("src", "")
            if src:
                image_sources.append(src)
            tag["style"] = STYLES["img"]
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in ("src", "alt", "style")}

        elif name == "a":
            tag["style"] = STYLES["a"]

        elif name == "code":
            if tag.parent and tag.parent.name == "pre":
                # Code block – handled at <pre> level below
                pass
            else:
                tag["style"] = STYLES["code_inline"]

        elif name == "pre":
            code_tag = tag.find("code")
            if code_tag:
                classes = code_tag.get("class") or tag.get("class") or []
                lang = ""
                for c in classes:
                    if c.startswith("language-"):
                        lang = c[9:]
                        break
                code_text = code_tag.get_text()
                new_html = _highlight_code(code_text, lang)
                tag.replace_with(BeautifulSoup(new_html, "html.parser"))

        elif name == "blockquote":
            tag["style"] = STYLES["blockquote"]

        elif name in ("ul", "ol"):
            tag["style"] = STYLES[name]

        elif name == "li":
            tag["style"] = STYLES["li"]

        elif name == "table":
            tag["style"] = STYLES["table"]
        elif name == "th":
            tag["style"] = STYLES["th"]
        elif name == "td":
            tag["style"] = STYLES["td"]

        elif name == "hr":
            tag["style"] = STYLES["hr"]

    wrapper = (
        '<section style="max-width:677px;margin:0 auto;padding:0 16px;'
        'font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',sans-serif;">'
        f'{soup}'
        '</section>'
    )
    return wrapper, image_sources


# ── Frontmatter & Metadata ────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML-like frontmatter from markdown. Returns (meta, body)."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    for line in fm_block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def extract_h1(md_text: str) -> tuple[str, str]:
    """Pull the first H1 out and return (title, remaining_text)."""
    lines = md_text.splitlines()
    title = ""
    rest = []
    found = False
    for line in lines:
        if not found and line.startswith("# "):
            title = line[2:].strip()
            found = True
        else:
            rest.append(line)
    return title, "\n".join(rest)


def auto_digest(html: str, max_bytes: int = 120) -> str:
    text = BeautifulSoup(html, "html.parser").get_text(" ")
    text = " ".join(text.split())
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Publish Markdown to WeChat draft box")
    parser.add_argument("markdown_file", help="Path to Markdown file")
    parser.add_argument("--cover", default="", help="Cover image: local path or URL")
    parser.add_argument("--author", default="", help="Article author")
    parser.add_argument("--digest", default="", help="Article summary")
    parser.add_argument("--dry-run", action="store_true", help="Save HTML locally, skip publishing")
    args = parser.parse_args()

    md_path = Path(args.markdown_file).resolve()
    if not md_path.exists():
        print(f"Error: file not found: {md_path}")
        sys.exit(1)

    raw = md_path.read_text(encoding="utf-8")
    base_dir = md_path.parent

    # Parse frontmatter
    meta, body = parse_frontmatter(raw)

    # Extract title
    title = meta.get("title", "")
    if not title:
        title, body = extract_h1(body)
    if not title:
        title = md_path.stem

    author = args.author or meta.get("author", "")
    cover_source = args.cover or meta.get("cover", "")

    print(f"Title  : {title}")
    print(f"Author : {author or '(none)'}")

    # Convert markdown body to WeChat HTML
    print("Converting Markdown → WeChat HTML ...")
    html_content, image_sources = md_to_wechat_html(body)
    print(f"Found {len(image_sources)} image(s) in content")

    # Use first content image as cover fallback
    if not cover_source and image_sources:
        cover_source = image_sources[0]
        print(f"Cover  : (using first content image)")
    elif cover_source:
        print(f"Cover  : {cover_source}")
    else:
        print("Cover  : (none – WeChat will use default)")

    digest = args.digest or meta.get("digest", "") or auto_digest(html_content)

    # Dry-run: just save HTML
    if args.dry_run:
        out = md_path.with_suffix(".wechat.html")
        out.write_text(html_content, encoding="utf-8")
        print(f"\nDry-run: HTML saved to {out}")
        return

    # Load credentials
    app_id, app_secret = load_config()

    # Get access token
    print("\nFetching access token ...")
    token = get_access_token(app_id, app_secret)

    # Upload content images and replace URLs
    if image_sources:
        print(f"Uploading {len(image_sources)} content image(s) ...")
        url_map: dict[str, str] = {}
        for src in image_sources:
            try:
                wechat_url = upload_image_for_content(src, token, base_dir)
                url_map[src] = wechat_url
                short = src[:60] + "..." if len(src) > 60 else src
                print(f"  ✓ {short}")
            except Exception as e:
                print(f"  ✗ Failed ({src[:60]}): {e}")
        for original, wechat_url in url_map.items():
            html_content = html_content.replace(original, wechat_url)

    # Upload cover image
    thumb_media_id = ""
    if cover_source:
        print("Uploading cover image ...")
        try:
            thumb_media_id = upload_thumb(cover_source, token, base_dir)
            print(f"  ✓ thumb_media_id: {thumb_media_id}")
        except Exception as e:
            print(f"  ✗ Cover upload failed: {e}")
            print("  Continuing without cover (WeChat may reject the draft).")

    # Build article payload
    article = {
        "title": title[:64],
        "author": author[:8],
        "digest": digest,
        "content": html_content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }

    # Publish
    print("\nPublishing to draft box ...")
    media_id = add_draft(article, token)
    print(f"\n✅ 已发布到草稿箱！")
    print(f"   media_id: {media_id}")
    print(f"\n前往草稿箱确认：https://mp.weixin.qq.com → 内容管理 → 草稿箱")


if __name__ == "__main__":
    main()
