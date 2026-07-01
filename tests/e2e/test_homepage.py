"""The homepage cards are pre-rendered at build time; app.js only filters/expands
them. These tests exercise that client behaviour against the real built site."""
import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def home(page: Page):
    page.goto("/")


def test_lists_all_brands_none_expanded(page: Page):
    cards = page.locator("#grid .card")
    expect(cards).to_have_count(58)
    expect(page.locator("#grid .card.open")).to_have_count(0)
    expect(page.locator("#meta")).to_contain_text("Showing all car brands.")


def test_search_filters_to_single_brand_and_auto_opens(page: Page):
    page.fill("#search", "bmw")
    expect(page.locator("#meta")).to_have_text('1 match for "bmw"')

    visible = page.locator("#grid .card:visible")
    expect(visible).to_have_count(1)
    card = visible.first
    expect(card.locator(".brand-name")).to_have_text("BMW")
    expect(card).to_have_class(re.compile(r"\bopen\b"))
    expect(card.locator(".card-head")).to_have_attribute("aria-expanded", "true")


def test_multiple_matches_do_not_auto_open(page: Page):
    page.fill("#search", "a")
    expect(page.locator("#meta")).to_contain_text("matches for")
    expect(page.locator("#grid .card.open")).to_have_count(0)
    # More than one visible, fewer than the full set.
    count = page.locator("#grid .card:visible").count()
    assert 1 < count < 58


def test_no_match_shows_contribute_prompt(page: Page):
    page.fill("#search", "zzzzz")
    expect(page.locator("#noresults")).to_be_visible()
    expect(page.locator("#nrq")).to_have_text("zzzzz")
    expect(page.locator("#grid .card:visible")).to_have_count(0)


def test_clearing_the_search_restores_all_brands(page: Page):
    page.fill("#search", "bmw")
    expect(page.locator("#grid .card:visible")).to_have_count(1)
    page.click("#clear")
    expect(page.locator("#search")).to_have_value("")
    expect(page.locator("#grid .card:visible")).to_have_count(58)
    expect(page.locator("#grid .card.open")).to_have_count(0)


def test_card_expands_and_collapses_on_click(page: Page):
    card = page.locator("#grid .card").filter(has_text="Toyota").first
    head = card.locator(".card-head")
    expect(card).not_to_have_class(re.compile(r"\bopen\b"))
    head.click()
    expect(card).to_have_class(re.compile(r"\bopen\b"))
    expect(head).to_have_attribute("aria-expanded", "true")
    expect(card.locator(".card-body .instruction").first).to_be_visible()
    head.click()
    expect(card).not_to_have_class(re.compile(r"\bopen\b"))


def test_unknown_brand_shows_help_needed_body(page: Page):
    page.fill("#search", "ferrari")
    card = page.locator("#grid .card:visible")
    expect(card).to_have_count(1)
    expect(card.locator(".tag.none")).to_have_text("Help needed")
    expect(card.locator(".unknown-body")).to_contain_text("Ferrari")


def test_copy_link_targets(page: Page):
    # Indexable brand copies its own page URL; card-only brand copies a homepage anchor.
    expect(page.locator("#brand-ford .card-link")).to_have_attribute(
        "data-link", "https://stopkeyless.com/disable-keyless-entry/ford/")
    expect(page.locator("#brand-ferrari .card-link")).to_have_attribute(
        "data-link", "https://stopkeyless.com/#brand-ferrari")


def test_copy_link_click_copies_without_expanding(page: Page):
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    card = page.locator("#brand-ford")
    btn = card.locator(".card-link")
    btn.click()
    expect(card).not_to_have_class(re.compile(r"\bopen\b"))   # copy must not expand
    expect(btn).to_have_class(re.compile(r"\bcopied\b"))
    assert page.evaluate("navigator.clipboard.readText()") == \
        "https://stopkeyless.com/disable-keyless-entry/ford/"


def test_brand_hash_deep_link_opens_card(page: Page):
    page.goto("/#brand-ferrari")
    expect(page.locator("#brand-ferrari")).to_have_class(re.compile(r"\bopen\b"))
