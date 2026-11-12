import { defineConfig, devices } from "@playwright/test";

const url = process.env.E2E_WEB_URL || "http://127.0.0.1:3000";
const isCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: ".",
  fullyParallel: false,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  workers: 1,
  timeout: 45_000,
  reporter: [["list"]],
  use: {
    baseURL: url,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "npm run start -- --hostname 127.0.0.1 --port 3000",
      cwd: "..",
      url: url + "/app",
      timeout: 120_000,
      reuseExistingServer: !isCI,
    },
    {
      command: "python -m uvicorn one_many_api.main:app --host 127.0.0.1 --port 8000",
      cwd: "../../api",
      url: "http://127.0.0.1:8000/api/v1/ready",
      env: {
        ENVIRONMENT: "test",
        AUTH_SECRET: "stage-seven-browser-test-credential-only-for-ci-123456",
        DATABASE_URL:
          process.env.E2E_DATABASE_URL ||
          "postgresql+psycopg://one_many:validation-only-not-real@127.0.0.1:5432/one_many",
        CORS_ORIGINS: '["http://127.0.0.1:3000","http://localhost:3000"]',
        PUBLIC_WEB_URL: "http://127.0.0.1:3000",
      },
      timeout: 120_000,
      reuseExistingServer: !isCI,
    },
  ],
});
