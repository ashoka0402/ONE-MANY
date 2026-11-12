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



test("product prototype: quotes, funding simulation, AG Grid, Bryntum, and animated handoff", async ({ page }) => {
  const suffix = Date.now().toString(36);
  await page.goto("/app");
  await page.getByLabel("Display name").fill("Prototype Member");
  await page.getByLabel("Email address").fill("prototype-" + suffix + "@example.com");
  await page.getByLabel("Password").fill("prototype-only-test-password");
  await page.locator("form.work-form").getByRole("button", { name: "Create account" }).click();

  await expect(page.getByRole("heading", { name: "Add a new need" })).toBeVisible();
  await page.getByRole("button", { name: /Explore complete prototype/ }).click();

  await expect(page.getByRole("heading", { name: "Understand the need." })).toBeVisible();
  await expect(page.getByText("DEMO · NOT REAL PAYMENTS")).toBeVisible();
  await page.getByRole("button", { name: "Sample extraction" }).first().click();
  await expect(page.getByText(/Sample classification · not a Gemini response/)).toBeVisible();

  const navigation = page.getByRole("navigation", { name: "Prototype navigation" });
  await navigation.getByRole("button", { name: /Draft quotes/ }).click();
  await expect(page.getByRole("heading", { name: "Saved draft quotes" })).toBeVisible();
  await page.locator(".pd-quote").filter({ hasText: "Portable projector" }).click();
  await expect(page.getByText("$120.00 each for 3")).toBeVisible();

  await navigation.getByRole("button", { name: /Group funding/ }).click();
  await expect(page.getByRole("heading", { name: "Fund a shared possibility." })).toBeVisible();
  await page.getByRole("button", { name: /Simulate approval/ }).click();
  await page.getByRole("button", { name: /Simulate capture/ }).click();
  await expect(page.locator(".pd-funding-summary")).toContainText("$240.00");

  await navigation.getByRole("button", { name: /Contribution ledger/ }).click();
  await expect(page.getByRole("heading", { name: "Every contribution. Accounted for." })).toBeVisible();
  await expect(page.getByText("Fictional participant contributions")).toBeVisible();
  await expect(page.getByText("Fictional event history")).toBeVisible();

  await navigation.getByRole("button", { name: /Scheduling/ }).click();
  await expect(page.getByRole("heading", { name: "One asset. Everyone's turn." })).toBeVisible();
  await expect(page.getByRole("region", { name: "Shared asset booking timeline" })).toBeVisible();
  await page.getByRole("button", { name: /Replay handoff/ }).click();
  await expect(page.getByText("From my turn to yours.")).toBeVisible();
  await page.screenshot({ path: "test-results/product-handoff-schedule.png", fullPage: true });

  await page.getByRole("button", { name: /Open live workspace/ }).click();
  await expect(page.getByRole("heading", { name: "Add a new need" })).toBeVisible();

  const liveNav = page.getByRole("navigation", { name: "Workspace navigation" });
  await liveNav.getByRole("button", { name: /Draft quotes/ }).click();
  await expect(page.getByRole("heading", { name: "Saved draft quotes" })).toBeVisible();
  await liveNav.getByRole("button", { name: /Group funding/ }).click();
  await expect(page.getByRole("heading", { name: "Fund a shared possibility." })).toBeVisible();
  await liveNav.getByRole("button", { name: /Contribution ledger/ }).click();
  await expect(page.getByRole("heading", { name: "Every contribution. Accounted for." })).toBeVisible();
  await liveNav.getByRole("button", { name: /Shared scheduling/ }).click();
  await expect(page.getByRole("heading", { name: "One asset. Everyone's turn." })).toBeVisible();
});
