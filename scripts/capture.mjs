// Capture the real generated report; every screenshot records the exact source/view.
import { chromium } from "@playwright/test";
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
const browser = await chromium.launch({ headless: true });
const captures = [];
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
