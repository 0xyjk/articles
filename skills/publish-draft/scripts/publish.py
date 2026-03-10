#!/usr/bin/env python3
"""
Publish a Markdown file to WeChat Official Account draft box.

Markdown → HTML conversion is handled by bm.md API (https://bm.md),
which produces WeChat-optimized HTML with proper inline styles.

Usage:
    python3 publish.py <markdown_file> [options]

Options:
    --cover PATH_OR_URL   Cover image (local path or https URL)
    --author NAME         Article author
    --digest TEXT         Article summary (auto-generated if omitted)
    --style NAME          bm.md markdownStyle theme (default: ayu-light)
    --code-theme NAME     bm.md codeTheme (default: kimbie-light)
    --dry-run             Save converted HTML locally without publishing

Config (searched in order):
    .publish-draft/.env   (project-level)
    ~/.publish-draft/.env (user-level)

.env format:
    WECHAT_APP_ID=wxxxxxxxxxxxxxxxxxxx
    WECHAT_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Requirements:
    pip install requests beautifulsoup4
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
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install requests beautifulsoup4")
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
    env = {}
    for path in [Path(".publish-draft/.env"), Path.home() / ".publish-draft" / ".env"]:
        env = load_env_file(path)
        if env:
            break
    app_id = os.environ.get("WECHAT_APP_ID") or env.get("WECHAT_APP_ID", "")
    app_secret = os.environ.get("WECHAT_APP_SECRET") or env.get("WECHAT_APP_SECRET", "")
    if not app_id or not app_secret:
        print("Error: Missing WECHAT_APP_ID or WECHAT_APP_SECRET.")
        print("Create .publish-draft/.env with:")
        print("  WECHAT_APP_ID=wxxxxxxxxxxxxxxxxxxx")
        print("  WECHAT_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)
    return app_id, app_secret


# ── bm.md API ─────────────────────────────────────────────────────────────────

def render_markdown(md_text: str, style: str = "ayu-light", code_theme: str = "kimbie-light") -> str:
    """Convert Markdown to WeChat-optimized HTML via bm.md API."""
    resp = requests.post(
        "https://bm.md/api/markdown/render",
        json={
            "markdown": md_text,
            "platform": "wechat",
            "markdownStyle": style,
            "codeTheme": code_theme,
            "enableFootnoteLinks": True,
            "openLinksInNewWindow": False,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"bm.md API error {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if "result" not in data:
        raise RuntimeError(f"bm.md unexpected response: {data}")
    html = data["result"]
    # bm.md encodes & as &#x26; but WeChat doesn't decode numeric HTML entities —
    # replace with &amp; which WeChat renders correctly as &.
    html = html.replace("&#x26;", "&amp;")
    return html


def extract_image_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [img["src"] for img in soup.find_all("img") if img.get("src")]


# ── WeChat API ────────────────────────────────────────────────────────────────

API_BASE = "https://api.weixin.qq.com"


def get_access_token(app_id: str, app_secret: str) -> str:
    resp = requests.get(f"{API_BASE}/cgi-bin/token", params={
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret,
    }, timeout=15)
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"get_access_token failed: {data}")
    return data["access_token"]


def upload_image_for_content(image_source: str, token: str, base_dir: Path) -> str:
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
    image_bytes, content_type = _fetch_image(image_source, base_dir)
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
    resp = requests.post(
        f"{API_BASE}/cgi-bin/draft/add",
        params={"access_token": token},
        data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"draft/add failed: {data}")
    return data["media_id"]


def _fetch_image(source: str, base_dir: Path) -> tuple[bytes, str]:
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


# ── Frontmatter & Metadata ────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
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


def _strip_md_inline(text: str) -> str:
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]*)\]\(.*?\)', r'\1', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    return text.strip()


def extract_h1(md_text: str) -> tuple[str, str]:
    lines = md_text.splitlines()
    title, rest, found = "", [], False
    for line in lines:
        if not found and line.startswith("# "):
            title = _strip_md_inline(line[2:].strip())
            found = True
        else:
            rest.append(line)
    return title, "\n".join(rest)


def auto_digest(html: str, max_bytes: int = 120) -> str:
    text = " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())
    encoded = text.encode("utf-8")
    return encoded[:max_bytes].decode("utf-8", errors="ignore") if len(encoded) > max_bytes else text


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Publish Markdown to WeChat draft box")
    parser.add_argument("markdown_file", help="Path to Markdown file")
    parser.add_argument("--cover", default="", help="Cover image: local path or URL")
    parser.add_argument("--author", default="", help="Article author")
    parser.add_argument("--digest", default="", help="Article summary")
    parser.add_argument("--style", default="ayu-light", help="bm.md markdownStyle (default: ayu-light)")
    parser.add_argument("--code-theme", default="kimbie-light", help="bm.md codeTheme (default: kimbie-light)")
    parser.add_argument("--dry-run", action="store_true", help="Save HTML locally, skip publishing")
    args = parser.parse_args()

    md_path = Path(args.markdown_file).resolve()
    if not md_path.exists():
        print(f"Error: file not found: {md_path}")
        sys.exit(1)

    raw = md_path.read_text(encoding="utf-8")
    base_dir = md_path.parent

    meta, body = parse_frontmatter(raw)

    title = meta.get("title", "")
    if not title:
        title, body = extract_h1(body)
    if not title:
        title = md_path.stem

    author = args.author or meta.get("author", "")
    cover_source = args.cover or meta.get("cover", "")

    print(f"Title  : {title}")
    print(f"Author : {author or '(none)'}")

    print(f"Converting via bm.md (style={args.style}) ...")
    html_content = render_markdown(body, style=args.style, code_theme=args.code_theme)
    image_sources = extract_image_urls(html_content)
    print(f"Found {len(image_sources)} image(s) in content")

    if not cover_source and image_sources:
        cover_source = image_sources[0]
        print(f"Cover  : (using first content image)")
    elif cover_source:
        print(f"Cover  : {cover_source}")

    digest = args.digest or meta.get("digest", "") or auto_digest(html_content)

    if args.dry_run:
        out = md_path.with_suffix(".wechat.html")
        out.write_text(html_content, encoding="utf-8")
        print(f"\nDry-run: HTML saved to {out}")
        return

    app_id, app_secret = load_config()

    print("\nFetching access token ...")
    token = get_access_token(app_id, app_secret)

    if image_sources:
        print(f"Uploading {len(image_sources)} content image(s) ...")
        url_map: dict[str, str] = {}
        for src in image_sources:
            try:
                wechat_url = upload_image_for_content(src, token, base_dir)
                url_map[src] = wechat_url
                print(f"  ✓ {src[:60]}{'...' if len(src)>60 else ''}")
            except Exception as e:
                print(f"  ✗ Failed ({src[:60]}): {e}")
        for original, wechat_url in url_map.items():
            html_content = html_content.replace(original, wechat_url)

    if not cover_source:
        print("\nError: 微信草稿箱发布必须提供封面图。")
        print("  --cover 图片路径或URL  /  frontmatter: cover: ./images/cover.png")
        sys.exit(1)
    print("Uploading cover image ...")
    try:
        thumb_media_id = upload_thumb(cover_source, token, base_dir)
        print(f"  ✓ thumb_media_id: {thumb_media_id}")
    except Exception as e:
        print(f"  ✗ Cover upload failed: {e}")
        sys.exit(1)

    article = {
        "title": title[:64],
        "author": author[:8],
        "digest": digest.encode("utf-8")[:120].decode("utf-8", errors="ignore"),
        "content": html_content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }

    print("\nPublishing to draft box ...")
    media_id = add_draft(article, token)
    print(f"\n✅ 已发布到草稿箱！")
    print(f"   media_id: {media_id}")
    print(f"\n前往草稿箱确认：https://mp.weixin.qq.com → 内容管理 → 草稿箱")


if __name__ == "__main__":
    main()
