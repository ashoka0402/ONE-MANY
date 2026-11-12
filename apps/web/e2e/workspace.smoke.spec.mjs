import { expect, test } from "@playwright/test";

test("real browser: registration, persisted need, and memory-only logout", async ({ page }) => {
  const testId = Date.now().toString(36);
  const needText = `Need a cordless drill to install a shelf safely, browser test ${testId}`;

  await page.goto("/");
  await expect(page).toHaveTitle(/ONE \/ MANY/);
  await page.screenshot({ path: "test-results/stage7-landing.png", fullPage: true });

  await page.goto("/app");
  await expect(page.getByRole("heading", { name: /get started/i })).toBeVisible();
  await page.getByLabel("Display name").fill("Automated Demo Member");
  await page.getByLabel("Email address").fill(`browser-${testId}@example.com`);
  await page.getByLabel("Password").fill("browser-ci-test-password-do-not-use");
  await page.locator("form.work-form").getByRole("button", { name: "Create account" }).click();

  await expect(page.getByRole("heading", { name: "Add a new need" })).toBeVisible();
  await page.getByLabel("What do you need?").fill(needText);
  await page.getByLabel("Neighborhood or general location (optional)").fill("Baner, Pune");
  await page.getByLabel("From (optional)").fill("2026-11-20");
  await page.getByLabel("Until (optional)").fill("2026-11-22");
  await page.locator("label.work-consent input[type=checkbox]").check();
  await page.getByRole("button", { name: /Save this need/ }).click();

  await expect(page.getByText(needText, { exact: true })).toBeVisible();
  await expect(page.getByText("Baner, Pune", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/stage7-workspace.png", fullPage: true });

  // Reload forgets the in-memory token, as designed; no hidden session data.
  await page.reload();
  await expect(page.getByRole("heading", { name: /get started/i })).toBeVisible();
  await expect(page.getByText(needText, { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Sign in", exact: true }).first().click();
  await page.getByLabel("Email address").fill(`browser-${testId}@example.com`);
  await page.getByLabel("Password").fill("browser-ci-test-password-do-not-use");
  await page.locator("form.work-form").getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText(needText, { exact: true })).toBeVisible();
});
