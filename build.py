#!/usr/bin/env python3
"""Static page generator for StopKeyless (see DESIGN.md, decisions D2 + D6).

Proof-of-concept scope: render ONE brand page (Ford by default) from the existing
data/cars.json through Jinja2 templates into dist/. The per-brand YAML migration
(DESIGN.md D3) is not done yet, so this reads cars.json directly and filters to the
requested brand.

Usage:
    .venv/bin/python build.py [BrandName]   # defaults to "Ford"
"""
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dist"
SITE_URL = "https://stopkeyless.com"
SITE_NAME = "StopKeyless"

TYPE_LABEL = {"temp": "Temporary", "auto": "Automatic", "perm": "Permanent", "info": "Note"}


def load_faqs():
    return json.loads((ROOT / "data" / "faqs.json").read_text(encoding="utf-8"))


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


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
    url = f"{SITE_URL}/disable-keyless-entry/{slug}/"
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


def main():
    brand_name = sys.argv[1] if len(sys.argv) > 1 else "Ford"
    cars = load_cars()
    car = find_brand(cars, brand_name)
    faqs = load_faqs()

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["TYPE_LABEL"] = TYPE_LABEL
    env.globals["SITE_NAME"] = SITE_NAME

    path, size = build_brand(env, car, faqs)
    print(f"Wrote {path.relative_to(ROOT)} ({size:,} bytes)")


if __name__ == "__main__":
    main()
