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


test("dark demo: five navigable sections, interactive preview, and real-mode escape", async ({ page }) => {
  const suffix = Date.now().toString(36);
  await page.goto("/app");
  await page.getByLabel("Display name").fill("Demo Tester");
  await page.getByLabel("Email address").fill("demo-preview-" + suffix + "@example.com");
  await page.getByLabel("Password").fill("demo-preview-password-not-real");
  await page.locator("form.work-form").getByRole("button", { name: "Create account" }).click();
  // The deployed build opens the real workspace first. Wait for sign-up
  // navigation to finish before locating the optional preview action.
  await expect(page.getByRole("heading", { name: "Add a new need" })).toBeVisible();
  await page.getByRole("button", { name: /Explore dark demo/i }).click();
  await expect(page.getByRole("heading", { name: /Good to see you/i })).toBeVisible();
  await expect(page.getByText("FICTIONAL DEMO").first()).toBeVisible();

  await page.getByRole("button", { name: "Flip card for details" }).click();
  await expect(page.getByText("Example equal share")).toBeVisible();
  await page.getByRole("button", { name: "Next need" }).click();
  await expect(page.getByText("Outdoor movie night", { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: /Your needs/ }).click();
  await expect(page.getByText("PREWRITTEN CLASSIFICATION").first()).toBeVisible();
  await page.getByRole("button", { name: /Match ready only/ }).click();
  await expect(page.getByText("Weekend pressure washer")).toBeVisible();

  await page.getByRole("button", { name: /Shared groups/ }).click();
  await expect(page.getByText("The clean-up crew")).toBeVisible();
  await page.getByRole("navigation", { name: "Demo navigation" }).getByRole("button", { name: "Contributions" }).click();
  await expect(page.getByText("67% scenario complete")).toBeVisible();

  await page.getByRole("button", { name: /Contribution ledger/ }).click();
  await expect(page.getByText("DEMO-1048")).toBeVisible();
  await expect(page.getByRole("button", { name: /Export demo CSV/ })).toBeVisible();

  await page.getByRole("button", { name: /Scheduling/ }).click();
  await expect(page.getByText("3 sample bookings")).toBeVisible();
  await page.getByRole("button", { name: "Sat 21" }).click();
  await expect(page.getByText("Portable projector", { exact: true })).toBeVisible();

  await page.screenshot({ path: "test-results/emerald-demo-workspace.png", fullPage: true });
  await page.getByRole("button", { name: /Live workspace/ }).last().click();
  await expect(page.getByRole("heading", { name: "Add a new need" })).toBeVisible();
});
