// Capture the real generated report; every screenshot records the exact source/view.
import { chromium } from "@playwright/test";
import { launchOptions } from "./browser-options.mjs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { platform, arch } from "node:os";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { resolve } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const source = JSON.parse(
    await readFile(resolve(root, "reports/run_manifest.json"), "utf8"),
);
const report = pathToFileURL(
    resolve(root, "docs/assets/carbon-report.html"),
).href;
const browser = await chromium.launch(launchOptions);
const captures = [];
const browserVersion = browser.version();
const captureSource = execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: root,
    encoding: "utf8",
}).trim();
try {
    for (const view of [
        {
            name: "report-desktop",
            width: 1440,
            height: 1000,
            geography: "WORLD",
            year: "2022",
        },
        {
            name: "report-ytd",
            width: 1440,
            height: 1000,
            geography: "WORLD",
            year: "2023",
        },
        {
            name: "report-mobile",
            width: 390,
            height: 844,
            geography: "China",
            year: "2022",
        },
    ]) {
        const page = await browser.newPage({
            viewport: { width: view.width, height: view.height },
            deviceScaleFactor: 1,
        });
        await page.goto(report);
        await page.locator("#geography").selectOption(view.geography);
        await page.locator("#year").selectOption(view.year);
        await page.locator("#total").waitFor();
        const path = resolve(root, "docs/assets/" + view.name + ".png");
        await page.screenshot({ path, fullPage: true });
        captures.push({
            ...view,
            path: "docs/assets/" + view.name + ".png",
            total: await page.locator("#total").textContent(),
            period: await page.locator("#period").textContent(),
            sha256: createHash("sha256")
                .update(await readFile(path))
                .digest("hex"),
        });
        await page.close();
    }
} finally {
    await browser.close();
}
await mkdir(resolve(root, "reports/local"), { recursive: true });
await writeFile(
    resolve(root, "reports/local/capture-manifest.json"),
    JSON.stringify(
        {
            source_git_sha: source.source_git_sha,
            capture_source_git_sha: captureSource,
            browser_version: browserVersion,
            playwright_version: JSON.parse(
                await readFile(
                    resolve(root, "node_modules/playwright/package.json"),
                    "utf8",
                ),
            ).version,
            platform: platform() + "/" + arch(),
            browser_provider: process.env.CARBON_CHROMIUM_EXECUTABLE
                ? "reviewed local executable override"
                : "Playwright pinned Chromium",
            report_sha256:
                source.generated_sha256["docs/assets/carbon-report.html"],
            captures,
            scope: "Actual Chromium capture of the Python companion HTML; not Power BI output.",
        },
        null,
        2,
    ) + "\n",
);
console.log("Captured " + captures.length + " actual report views.");
