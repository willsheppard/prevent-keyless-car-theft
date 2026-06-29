const { test, expect } = require("@playwright/test");

// Pre-rendered, individually indexable brand pages (the point of the migration).

test("a known brand page renders its content and metadata", async ({ page }) => {
  const res = await page.goto("/disable-keyless-entry/ford/");
  expect(res.status()).toBe(200);

  await expect(page).toHaveTitle(/disable keyless entry on a Ford/i);
  await expect(page.locator("h1")).toContainText("Ford");
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
    "href", "https://stopkeyless.com/disable-keyless-entry/ford/");

  // At least one instruction with the step list, the legend, and the FAQ.
  await expect(page.locator(".brand-instructions .instruction").first()).toBeVisible();
  await expect(page.locator(".legend")).toBeVisible();
  await expect(page.locator(".faq").first()).toBeVisible();

  // BreadcrumbList structured data is embedded.
  const ld = await page.locator('script[type="application/ld+json"]').first().textContent();
  expect(ld).toContain("BreadcrumbList");
});

test("breadcrumb links back to the homepage finder", async ({ page }) => {
  await page.goto("/disable-keyless-entry/ford/");
  await page.locator('.breadcrumb a[href="/"]').click();
  await expect(page).toHaveURL("http://localhost:4173/");
  await expect(page.locator("#grid .card")).toHaveCount(58);
});

test("a gated-out (unknown) brand has no standalone page", async ({ page }) => {
  const res = await page.goto("/disable-keyless-entry/ferrari/");
  expect(res.status()).toBe(404);
});

test("sitemap lists the homepage and known brands only", async ({ page }) => {
  const res = await page.goto("/sitemap.xml");
  const xml = await res.text();
  expect(xml).toContain("<loc>https://stopkeyless.com/</loc>");
  expect(xml).toContain("disable-keyless-entry/ford/");
  // Unknown brands are excluded from the sitemap.
  expect(xml).not.toContain("disable-keyless-entry/ferrari/");
});
