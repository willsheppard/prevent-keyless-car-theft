#!/usr/bin/env python3
"""Static site generator for StopKeyless (see DESIGN.md, decisions D2 + D6).

Builds the complete site into dist/:
  - the homepage (index.html) with all brand cards pre-rendered,
  - one indexable page per known brand (disable-keyless-entry/<slug>/),
  - the static assets (css/ js/ img/ data/),
  - sitemap.xml (indexable pages only, per the DESIGN.md §6 content gate),
  - robots.txt.

All brand data is read from the single data/cars.json.

Usage:
    .venv/bin/python scripts/build.py        # build the whole site into dist/
    .venv/bin/python scripts/build.py Ford   # build only the homepage + the Ford page
"""
import json
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"
SITE_URL = "https://stopkeyless.com"
SITE_NAME = "StopKeyless"

# Static asset directories copied verbatim into dist/. `data/` keeps the public
# dataset (and faqs) reachable at its existing URL; the homepage no longer fetches
# it (cards are pre-rendered), but external links and consumers still resolve.
ASSET_DIRS = ["css", "js", "img", "data"]

TYPE_LABEL = {"temp": "Temporary", "auto": "Automatic", "perm": "Permanent", "info": "Note"}

# Minimum body word count for a brand page to be indexable (DESIGN.md §6).
# Set to 1 so every brand with any content still publishes; raise later to gate
# out genuinely thin pages.
MIN_BODY_WORDS = 1


def load_faqs():
    return json.loads((ROOT / "data" / "faqs.json").read_text(encoding="utf-8"))


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def initials(name):
    """Two-letter monogram for a brand logo. Mirrors initials() in js/app.js: first
    letters of the first two words, else the first two letters."""
    clean = re.sub(r"[^A-Za-zÀ-ž ]", "", name).strip()
    parts = re.split(r"\s+", clean)
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return clean[:2].upper()


def model_names(aliases):
    """Title-case the alias list into display model names, de-duplicated."""
    out = []
    for a in aliases:
        name = a.title()
        if name not in out:
            out.append(name)
    return out


def load_cars():
    data = json.loads((ROOT / "data" / "cars.json").read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("cars", data)


def find_brand(cars, name):
    for car in cars:
        if car.get("name", "").lower() == name.lower():
            return car
    raise SystemExit(f"Brand not found in cars.json: {name!r}")


def body_word_count(car):
    """Count words in a brand's visible body text (DESIGN.md §6 thin-content gate):
    instruction prose, steps, sub-section labels/steps, notes, model scope, and the
    standalone info boxes. HTML tags are stripped first so markup isn't counted."""
    chunks = []
    for instr in car.get("instructions", []):
        chunks.append(instr.get("text", ""))
        chunks.append(instr.get("models", ""))
        chunks.extend(instr.get("steps", []))
        chunks.extend(instr.get("notes", []))
        for sub in instr.get("sub", []):
            chunks.append(sub.get("label", ""))
            chunks.extend(sub.get("steps", []))
    chunks.extend(car.get("info", []))
    text = re.sub(r"<[^>]+>", " ", " ".join(chunks))
    return len(text.split())


def is_indexable(car):
    """Content gate (DESIGN.md §6). A brand earns its own indexable page only if it
    is not flagged `unknown`, has at least one instruction with steps, and clears the
    minimum body word count. The 21 `unknown` brands stay a contribution funnel
    (homepage cards), not thin pages."""
    if car.get("unknown"):
        return False
    if not any(i.get("steps") for i in car.get("instructions", [])):
        return False
    return body_word_count(car) >= MIN_BODY_WORDS


def brand_url(car):
    return f"{SITE_URL}/disable-keyless-entry/{slugify(car['name'])}/"


def build_embedded_metadata(brand, url):
    """Embedded metadata (JSON-LD) for search engines. Only BreadcrumbList still
    earns a rich result; Google dropped HowTo (2023) and FAQ (2026) rich results."""
    blobs = [
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": brand, "item": url},
            ],
        }
    ]
    return [json.dumps(b, ensure_ascii=False) for b in blobs]


def build_brand(env, car, faqs):
    brand = car["name"]
    slug = slugify(brand)
    url = brand_url(car)
    instructions = car.get("instructions", [])
    info = car.get("info", [])
    models = model_names(car.get("aliases", []))

    model_faqs = [faq for faq in faqs if faq.get("on_model_page")]

    # Brand prose (subtitle, intro, title/meta patterns) lives in brand.html.j2,
    # interpolating {{ brand }}; build_brand passes only data.
    html = env.get_template("brand.html.j2").render(
        brand=brand,
        canonical=url,
        instructions=instructions,
        info=info,
        aliases_text=", ".join(models),
        faqs=model_faqs,
        embedded_metadata=build_embedded_metadata(brand, url),
    )

    out_path = OUT / "disable-keyless-entry" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path, len(html)


def build_index(env, cars, faqs):
    """Render the homepage with all brand cards pre-rendered into the grid.
    js/app.js now only filters/expands these cards. Cards are sorted by name
    (case-insensitive, matching the JS localeCompare order); `idx` is the original
    data position so the aria-controls/id pairing stays stable."""
    cards = []
    for idx, car in sorted(enumerate(cars), key=lambda pair: pair[1]["name"].lower()):
        name = car["name"]
        instructions = car.get("instructions", [])
        cards.append({
            "idx": idx,
            "name": name,
            "initials": initials(name),
            "search": " ".join([name, *car.get("aliases", [])]).lower(),
            "unknown": bool(car.get("unknown")),
            # Unique instruction types, first-seen order (mirrors tagsFor()).
            "tag_types": list(dict.fromkeys(i["type"] for i in instructions)),
            "instructions": instructions,
            "info": car.get("info", []),
        })

    html = env.get_template("index.html.j2").render(
        canonical=SITE_URL + "/",
        cards=cards,
        faqs=faqs,
    )
    out_path = OUT / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path, len(html)


def build_sitemap(indexable):
    """sitemap.xml of indexable URLs only: the homepage plus each gated brand page."""
    urls = [SITE_URL + "/"] + [brand_url(car) for car in indexable]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")
    path = OUT / "sitemap.xml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, len(urls)


def build_robots():
    path = OUT / "robots.txt"
    path.write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    return path


def copy_assets():
    """Copy the static asset dirs (and CNAME) verbatim into dist/."""
    for name in ASSET_DIRS:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, OUT / name, dirs_exist_ok=True)
    cname = ROOT / "CNAME"
    if cname.is_file():
        shutil.copy2(cname, OUT / "CNAME")


def make_env():
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["TYPE_LABEL"] = TYPE_LABEL
    env.globals["SITE_NAME"] = SITE_NAME
    return env


def build_site(only_brand=None):
    """Build the whole site into dist/. If only_brand is given, build just the
    homepage and that one brand page (fast local preview) and skip assets/sitemap."""
    cars = load_cars()
    faqs = load_faqs()
    env = make_env()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    idx_path, idx_size = build_index(env, cars, faqs)
    print(f"Wrote {idx_path.relative_to(ROOT)} ({idx_size:,} bytes)")

    if only_brand:
        car = find_brand(cars, only_brand)
        path, size = build_brand(env, car, faqs)
        print(f"Wrote {path.relative_to(ROOT)} ({size:,} bytes)")
        return

    indexable = [car for car in cars if is_indexable(car)]
    for car in indexable:
        build_brand(env, car, faqs)
    print(f"Wrote {len(indexable)} brand pages "
          f"({len(cars) - len(indexable)} brands gated out as cards only)")

    copy_assets()
    print(f"Copied assets: {', '.join(ASSET_DIRS)}")

    _, n = build_sitemap(indexable)
    print(f"Wrote sitemap.xml ({n} URLs)")
    build_robots()
    print("Wrote robots.txt")


def main():
    only_brand = sys.argv[1] if len(sys.argv) > 1 else None
    build_site(only_brand=only_brand)


if __name__ == "__main__":
    main()
