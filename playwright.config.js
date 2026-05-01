const { defineConfig } = require("@playwright/test");
const { getSmokeRuntime } = require("./e2e/runtime");

const runtime = getSmokeRuntime();

module.exports = defineConfig({
  testDir: "./e2e",
  testMatch: /.*\.spec\.js$/,
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: {
    timeout: 15_000,
  },
  reporter: [
    ["list"],
    ["html", { open: "never" }],
  ],
  outputDir: "test-results",
  use: {
    baseURL: runtime.baseUrl,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  globalSetup: require.resolve("./e2e/global-setup"),
  globalTeardown: require.resolve("./e2e/global-teardown"),
  projects: [
    {
      name: "chromium",
      use: {
        browserName: "chromium",
        launchOptions: runtime.executablePath
          ? {
              executablePath: runtime.executablePath,
            }
          : {},
      },
    },
  ],
});
