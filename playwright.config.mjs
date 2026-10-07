import { defineConfig } from "@playwright/test";
import { launchOptions } from "./scripts/browser-options.mjs";

export default defineConfig({
    testDir: "./tests",
    testMatch: "report.spec.mjs",
    retries: 0,
    workers: 1,
    reporter: [
        ["list"],
        ["json", { outputFile: "reports/local/browser-tests.json" }],
    ],
    outputDir: "reports/local/browser-output",
    use: { launchOptions },
});
