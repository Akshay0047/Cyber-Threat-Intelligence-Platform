import { expect, test } from "@playwright/test";

const PAGES = [
  { path: "/search", heading: "Indicator search" },
  { path: "/entities", heading: "Entities" },
  { path: "/graph", heading: "Graph queries" },
  { path: "/analytics", heading: "Analytics" },
];

function intersects(a, b) {
  const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
  const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
  return overlapX > 8 && overlapY > 8;
}

async function assertNoOverlap(page) {
  const boxes = await page.locator("h1, nav a, nav button, form button, table th").evaluateAll((elements) =>
    elements
      .filter((element) => {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      })
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          text: (element.textContent || "").trim().slice(0, 40),
          top: rect.top,
          left: rect.left,
          right: rect.right,
          bottom: rect.bottom,
        };
      })
  );

  const collisions = [];
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i];
      const b = boxes[j];
      if (a.text === b.text) continue;
      if (intersects(a, b)) collisions.push(`${a.text} overlaps ${b.text}`);
    }
  }
  expect(collisions, collisions.join("\n")).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Username").fill("admin");
  await page.getByLabel("Password").fill("cti-lab-2026");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Indicator search" })).toBeVisible();
});

test("login card does not crowd the viewport", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/login");
  const card = page.locator("form");
  await expect(card).toBeVisible();
  const box = await card.boundingBox();
  const viewport = page.viewportSize();
  expect(box.x).toBeGreaterThan(8);
  expect(box.y).toBeGreaterThan(8);
  expect(box.x + box.width).toBeLessThan(viewport.width - 8);
  expect(box.y + box.height).toBeLessThan(viewport.height - 8);
});

for (const item of PAGES) {
  test(`${item.heading} lays out without overlapping controls`, async ({ page }) => {
    await page.goto(item.path);
    await expect(page.getByRole("heading", { name: item.heading })).toBeVisible();
    await assertNoOverlap(page);
  });
}

test("search, entities, graph, and analytics all render data", async ({ page }) => {
  await page.goto("/search");
  await page.getByPlaceholder("IP, domain, hash, or INF-01").fill("INF-01");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("heading", { name: /Infrastructure/ })).toBeVisible();

  await page.goto("/entities");
  await expect(page.getByRole("cell", { name: "INC-01" })).toBeVisible();
  await page.getByRole("combobox").selectOption("relationships");
  await expect(page.getByRole("button", { name: "Edit" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Delete" }).first()).toBeVisible();
  await page.getByRole("combobox").selectOption("graph-actors");
  await expect(page.getByRole("cell", { name: "TA-01" })).toBeVisible();

  await page.goto("/graph");
  await page.getByRole("button", { name: "Shortest path" }).click();
  await expect(page.getByText(/Shortest path: \d+ hop/)).toBeVisible();

  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "Severity breakdown" })).toBeVisible();
  await expect(page.getByText("Critical", { exact: true })).toBeVisible();
  await expect(page.getByText("Low", { exact: true })).toBeVisible();
});
