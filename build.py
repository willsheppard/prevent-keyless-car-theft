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

# Defined once; rendered as both visible FAQ and FAQPage JSON-LD.
FAQS = [
    {
        "q": "If I disable keyless entry, how do I get into my car?",
        "a": "You simply press the unlock button on your key fob, like cars have done for "
             "years. “Keyless” (or “passive”) entry just means the car "
             "unlocks automatically when the fob is nearby — turning it off only "
             "removes that automatic part. Pressing the button still works normally.",
    },
    {
        "q": "What about a Faraday pouch, or keeping keys far away?",
        "a": "A Faraday pouch can block the signal, but they’re easy to forget and "
             "often stop working over time. Keeping keys across the house doesn’t help "
             "much — the signal can still be relayed. Disabling keyless entry at the "
             "fob is more reliable and costs nothing.",
    },
    {
        "q": "The steps for my model are missing or wrong",
        "a": "This is a free community project and the list is always growing. If you can "
             "confirm the method for your model — or spot a correction — please "
             "use the contribute form on the home page. Some entries are marked unverified; "
             "always double-check against your own car’s manual.",
    },
]


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


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text)


def build_jsonld(brand, url, methods, faqs):
    """BreadcrumbList + a HowTo per method with steps + FAQPage."""
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
    for m in methods:
        steps = m.get("steps")
        if not steps:
            continue
        name = f"Disable keyless entry on a {brand}"
        if m.get("models"):
            name += f" ({m['models']})"
        elif TYPE_LABEL.get(m["type"]):
            name += f" ({TYPE_LABEL[m['type']].lower()})"
        blobs.append({
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": name,
            "step": [
                {"@type": "HowToStep", "position": i + 1, "text": strip_tags(s)}
                for i, s in enumerate(steps)
            ],
        })
    blobs.append({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
            }
            for f in faqs
        ],
    })
    return [json.dumps(b, ensure_ascii=False) for b in blobs]


def build_brand(env, car):
    brand = car["name"]
    slug = slugify(brand)
    url = f"{SITE_URL}/disable-keyless-entry/{slug}/"
    methods = car.get("methods", [])
    models = model_names(car.get("aliases", []))

    subtitle = (
        f"Thieves can unlock and start a keyless {brand} in seconds with a relay attack "
        f"— without ever touching your key. {brand} builds in free ways to switch "
        f"keyless entry off. Here’s how."
    )
    intro_html = (
        f"<p>Many {brand} models with keyless entry can be stolen by a <em>relay "
        f"attack</em>: two thieves use cheap radio equipment to extend the signal from "
        f"your key fob — sitting indoors near your front door — until the car "
        f"believes the key is right beside it. The car unlocks and starts, and they drive "
        f"off silently in under a minute.</p>"
        f"<p>The good news is you don’t need to buy anything. Depending on your model "
        f"and year, {brand} lets you suspend keyless entry automatically or turn it off "
        f"entirely. Choose the method below that matches your {brand}, and if you have "
        f"more than one key fob, repeat it for each one.</p>"
    )

    html = env.get_template("brand.html.j2").render(
        brand=brand,
        canonical=url,
        title=f"How to disable keyless entry on a {brand} — free | {SITE_NAME}",
        og_title=f"Stop your {brand} being stolen — disable keyless entry",
        meta_description=(
            f"Free, manufacturer-approved ways to disable keyless entry on your {brand} "
            f"and stop relay theft. Simple step-by-step instructions for {brand} models."
        ),
        subtitle=subtitle,
        intro_html=intro_html,
        methods=methods,
        aliases_text=", ".join(models),
        faqs=FAQS,
        jsonld=build_jsonld(brand, url, methods, FAQS),
    )

    out_path = OUT / "disable-keyless-entry" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path, len(html)


def main():
    brand_name = sys.argv[1] if len(sys.argv) > 1 else "Ford"
    cars = load_cars()
    car = find_brand(cars, brand_name)

    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["TYPE_LABEL"] = TYPE_LABEL

    path, size = build_brand(env, car)
    print(f"Wrote {path.relative_to(ROOT)} ({size:,} bytes)")


if __name__ == "__main__":
    main()
