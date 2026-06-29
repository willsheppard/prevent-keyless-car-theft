const { test, expect } = require("@playwright/test");

// The homepage cards are pre-rendered at build time; app.js only filters/expands
// them. These tests exercise that client behaviour against the real built site.

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("lists all brands on load, none expanded", async ({ page }) => {
  const cards = page.locator("#grid .card");
  await expect(cards).toHaveCount(58);
  await expect(cards.filter({ has: page.locator(":scope.open") })).toHaveCount(0);
  await expect(page.locator("#meta")).toContainText("Showing all 58 car makes");
});

test("search filters to a single brand and auto-opens it", async ({ page }) => {
  await page.fill("#search", "bmw");
  await expect(page.locator("#meta")).toHaveText('1 match for "bmw"');

  const visible = page.locator("#grid .card:visible");
  await expect(visible).toHaveCount(1);
  const card = visible.first();
  await expect(card.locator(".brand-name")).toHaveText("BMW");
  await expect(card).toHaveClass(/open/);
  await expect(card.locator(".card-head")).toHaveAttribute("aria-expanded", "true");
});

test("multiple matches do not auto-open", async ({ page }) => {
  await page.fill("#search", "a");
  await expect(page.locator("#meta")).toContainText("matches for");
  await expect(page.locator("#grid .card.open")).toHaveCount(0);
  // More than one visible, fewer than the full set.
  const count = await page.locator("#grid .card:visible").count();
  expect(count).toBeGreaterThan(1);
  expect(count).toBeLessThan(58);
});

test("no match shows the contribute prompt", async ({ page }) => {
  await page.fill("#search", "zzzzz");
  await expect(page.locator("#noresults")).toBeVisible();
  await expect(page.locator("#nrq")).toHaveText("zzzzz");
  await expect(page.locator("#grid .card:visible")).toHaveCount(0);
});

test("clearing the search restores all brands", async ({ page }) => {
  await page.fill("#search", "bmw");
  await expect(page.locator("#grid .card:visible")).toHaveCount(1);
  await page.click("#clear");
  await expect(page.locator("#search")).toHaveValue("");
  await expect(page.locator("#grid .card:visible")).toHaveCount(58);
  await expect(page.locator("#grid .card.open")).toHaveCount(0);
});

test("a card expands and collapses on click", async ({ page }) => {
  const card = page.locator("#grid .card").filter({ hasText: "Toyota" }).first();
  const head = card.locator(".card-head");
  await expect(card).not.toHaveClass(/open/);
  await head.click();
  await expect(card).toHaveClass(/open/);
  await expect(head).toHaveAttribute("aria-expanded", "true");
  await expect(card.locator(".card-body .instruction").first()).toBeVisible();
  await head.click();
  await expect(card).not.toHaveClass(/open/);
});

test("an unknown brand shows the help-needed body, not instructions", async ({ page }) => {
  await page.fill("#search", "ferrari");
  const card = page.locator("#grid .card:visible");
  await expect(card).toHaveCount(1);
  await expect(card.locator(".tag.none")).toHaveText("Help needed");
  await expect(card.locator(".unknown-body")).toContainText("Ferrari");
});
