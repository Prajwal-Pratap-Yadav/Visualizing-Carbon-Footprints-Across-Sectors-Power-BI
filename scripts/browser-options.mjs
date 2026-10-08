// Default to Playwright's pinned browser; allow a reviewed local executable for offline QA.
export const launchOptions = {
    headless: true,
    ...(process.env.CARBON_CHROMIUM_EXECUTABLE
        ? {
              executablePath: process.env.CARBON_CHROMIUM_EXECUTABLE,
              args: JSON.parse(process.env.CARBON_CHROMIUM_ARGS || "[]"),
          }
        : {}),
};
