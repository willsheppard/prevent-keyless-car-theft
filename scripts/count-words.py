#!/usr/bin/env python3
"""Report the body word count of every brand (DESIGN.md §6 thin-content gate).

Reuses build.body_word_count so the numbers match what the gate sees. Brands are
listed thinnest-first; the trailing column flags whether the brand is indexable.

Usage:
    .venv/bin/python scripts/count-words.py            # all brands
    .venv/bin/python scripts/count-words.py --indexable # only published brands
"""
import sys

import build

cars = build.load_cars()
if "--indexable" in sys.argv[1:]:
    cars = [car for car in cars if build.is_indexable(car)]

for car in sorted(cars, key=build.body_word_count):
    flag = "indexable" if build.is_indexable(car) else "card-only"
    print(f"{build.body_word_count(car):5d}  {flag:10}  {car['name']}")
