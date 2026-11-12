import { expect, test } from "@playwright/test";

test("landing: rich hero, scenario switcher, interactive split, FAQs and mobile navigation", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("#lp-main-title")).toContainText("Make it ours.");
  await expect(page.getByText("THE POSSIBILITY ENGINE")).toBeVisible();

  await page.getByRole("button", { name: /02 Portable projector/ }).click();
  await expect(page.getByText("A projector for our film nights.")).toBeVisible();
  await expect(page.getByText("$120.00").first()).toBeVisible();

  await page.getByRole("button", { name: "3", exact: true }).click();
  await expect(page.locator(".lp-calc-result")).toContainText("$133.33");

  await page.getByRole("button", { name: "What does Gemini actually do?" }).click();
  await expect(page.getByText(/Gemini extracts structured information/)).toBeVisible();

  await expect(page.getByRole("link", { name: /Discover what's possible/ })).toHaveAttribute("href", "/app");
  await page.screenshot({ path: "test-results/landing-emerald-desktop.png", fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open menu" }).click();
  await expect(page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "The experience" })).toBeVisible();
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "The experience" }).click();
  await expect(page.getByRole("button", { name: "Open menu" })).toBeVisible();
  await page.screenshot({ path: "test-results/landing-emerald-mobile.png", fullPage: true });
});
