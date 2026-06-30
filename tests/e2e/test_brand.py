"""Pre-rendered, individually indexable brand pages: one indexable URL per brand."""
import re

from playwright.sync_api import Page, expect


def test_known_brand_page_renders_content_and_metadata(page: Page):
    res = page.goto("/disable-keyless-entry/ford/")
    assert res.status == 200

    expect(page).to_have_title(re.compile("disable keyless entry on a Ford", re.I))
    expect(page.locator("h1")).to_contain_text("Ford")
    expect(page.locator('link[rel="canonical"]')).to_have_attribute(
        "href", "https://stopkeyless.com/disable-keyless-entry/ford/")

    # At least one instruction with the step list, the legend, and the FAQ.
    expect(page.locator(".brand-instructions .instruction").first).to_be_visible()
    expect(page.locator(".legend")).to_be_visible()
    expect(page.locator(".faq").first).to_be_visible()

    # BreadcrumbList structured data is embedded.
    ld = page.locator('script[type="application/ld+json"]').first.text_content()
    assert "BreadcrumbList" in ld


def test_breadcrumb_links_back_to_the_homepage_finder(page: Page):
    page.goto("/disable-keyless-entry/ford/")
    page.locator('.breadcrumb a[href="/"]').click()
    expect(page).to_have_url("http://localhost:4173/")
    expect(page.locator("#grid .card")).to_have_count(58)


def test_gated_out_unknown_brand_has_no_standalone_page(page: Page):
    res = page.goto("/disable-keyless-entry/ferrari/")
    assert res.status == 404


def test_sitemap_lists_homepage_and_known_brands_only(page: Page):
    res = page.goto("/sitemap.xml")
    xml = res.text()
    assert "<loc>https://stopkeyless.com/</loc>" in xml
    assert "disable-keyless-entry/ford/" in xml
    # Unknown brands are excluded from the sitemap.
    assert "disable-keyless-entry/ferrari/" not in xml
