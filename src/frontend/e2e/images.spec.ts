import { test, expect } from "@playwright/test";

test.use({ storageState: "playwright/.auth/user.json" });

const images = [
  {
    id: "sha256:aaa111bbb222",
    tags: ["nginx:latest"],
    author: "",
    create_time: "2024-01-15T08:00:00Z",
    size: 187000000,
  },
  {
    id: "sha256:ccc333ddd444",
    tags: ["postgres:16"],
    author: "postgres",
    create_time: "2024-01-14T08:00:00Z",
    size: 431000000,
  },
];

test.describe("Images", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/health", async (route) => {
      await route.fulfill({ json: { status: "ok", version: process.env.DOCKORE_VERSION! } });
    });
    await page.route("**/api/auth/validate", async (route) => {
      await route.fulfill({ json: { valid: true } });
    });
    await page.route("**/api/images**", async (route, request) => {
      if (request.method() === "GET") {
        return route.fulfill({ json: images });
      }
      await route.continue();
    });
  });

  test("renders image list", async ({ page }) => {
    await page.goto("/images");
    await expect(page.locator("text=nginx:latest")).toBeVisible();
    await expect(page.locator("text=postgres:16")).toBeVisible();
    await expect(page.getByRole("cell", { name: "postgres", exact: true })).toBeVisible();
  });

  test("opens pull modal", async ({ page }) => {
    await page.goto("/images");
    await expect(page.locator("text=nginx:latest")).toBeVisible();

    await page.getByRole("button", { name: "拉取镜像" }).click();
    await expect(page.locator(".ant-modal")).toBeVisible();
    await expect(page.getByPlaceholder("搜索 Docker Hub")).toBeVisible();
    await expect(page.locator(".ant-modal").getByText("搜索结果")).toBeVisible();
  });
});
