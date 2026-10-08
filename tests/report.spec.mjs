import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { resolve } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const url = pathToFileURL(resolve(root, "docs/assets/carbon-report.html")).href;
const data = JSON.parse(
    await readFile(resolve(root, "reports/report-data.json"), "utf8"),
);
const formatted = (v) =>
    new Intl.NumberFormat("en-GB", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(Number(v));

test("Every available geography/period displays the computed total and correct date length", async ({
    page,
}) => {
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(url);
    await expect(page.locator("#geography")).not.toHaveAttribute("multiple");
    for (const geography of data.geography_order) {
        await page.locator("#geography").selectOption(geography);
        for (const [year, period] of Object.entries(
            data.views[geography].periods,
        )) {
            await page.locator("#year").selectOption(year);
            await expect(page.locator("#total")).toHaveText(
                formatted(period.total) + " Mt",
            );
            await expect(page.locator("#days")).toHaveText(String(period.days));
            await expect(page.locator("#monthly-table tbody tr")).toHaveCount(
                period.months.length,
            );
            if (!period.complete)
                await expect(page.locator("#period")).toContainText(
                    "not annualised",
                );
        }
    }
    expect(errors).toEqual([]);
});

test("2023 explicitly compares Jan–May and exposes a readable numeric table", async ({
    page,
}) => {
    await page.goto(url);
    await page.locator("#year").selectOption("2023");
    await expect(page.locator("#change-label")).toHaveText(
        "Calendar-matched YTD YoY",
    );
    await expect(page.locator("#change")).toHaveText("+0.34%");
    await expect(page.locator("#change-note")).toContainText("Jan–May");
    await page
        .getByText("Inspect the monthly figures", { exact: true })
        .click();
    await expect(page.locator("#monthly-table")).toBeVisible();
    await expect(page.locator("#monthly-table tbody tr")).toHaveCount(5);
    await expect(page.locator("#chart")).toHaveAccessibleName(
        /Monthly six-sector CO2 totals/,
    );
});

for (const width of [1440, 768, 390]) {
    test(
        "Report has no page overflow or serious/critical axe violations at " +
            width +
            "px",
        async ({ page }) => {
            await page.setViewportSize({ width, height: 900 });
            await page.goto(url);
            const overflow = await page.evaluate(
                () => document.documentElement.scrollWidth > window.innerWidth,
            );
            expect(overflow).toBe(false);
            const results = await new AxeBuilder({ page }).analyze();
            expect(
                results.violations.filter((v) =>
                    ["serious", "critical"].includes(v.impact),
                ),
            ).toEqual([]);
        },
    );
}

test("The offline report requests no network resources", async ({ page }) => {
    const requests = [];
    page.on("request", (request) => {
        if (/^https?:/.test(request.url())) requests.push(request.url());
    });
    await page.goto(url);
    await page.locator("#geography").selectOption("India");
    expect(requests).toEqual([]);
});
