import { test, expect } from "@playwright/test";

test.use({ storageState: "playwright/.auth/user.json" });

const containers = [
  {
    id: "abc123def4567890",
    name: "web-1",
    image: {
      id: "sha256:111aaa",
      tags: ["nginx:latest"],
      author: "",
      create_time: "2024-01-15T08:00:00Z",
      size: 187000000,
    },
    create_time: "2024-01-15T08:00:00Z",
    status: "running",
  },
  {
    id: "bcd234efg5678901",
    name: "db-1",
    image: {
      id: "sha256:222bbb",
      tags: ["postgres:16"],
      author: "",
      create_time: "2024-01-14T08:00:00Z",
      size: 431000000,
    },
    create_time: "2024-01-14T08:00:00Z",
    status: "exited",
  },
];

test.describe("Containers", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/health", async (route) => {
      await route.fulfill({ json: { status: "ok", version: process.env.DOCKORE_VERSION! } });
    });
    await page.route("**/api/auth/validate", async (route) => {
      await route.fulfill({ json: { valid: true } });
    });
  });

  test("renders container list", async ({ page }) => {
    await page.route("**/api/containers**", async (route, request) => {
      if (request.method() === "GET") {
        return route.fulfill({ json: containers });
      }
      await route.continue();
    });

    await page.goto("/containers");
    await expect(page.locator("text=web-1")).toBeVisible();
    await expect(page.locator("text=db-1")).toBeVisible();
    await expect(page.locator("text=nginx:latest")).toBeVisible();
  });

  test("batch deletes selected containers", async ({ page }) => {
    let deletedIds: string[] | null = null;
    await page.route("**/api/containers**", async (route, request) => {
      if (request.method() === "DELETE") {
        deletedIds = request.postDataJSON().ids;
        return route.fulfill({ json: { deleted: deletedIds, failed: {} } });
      }
      if (request.method() === "GET") {
        return route.fulfill({ json: deletedIds ? [] : containers });
      }
      await route.continue();
    });

    await page.goto("/containers");
    await expect(page.locator("text=web-1")).toBeVisible();

    await page.locator(".ant-table-thead .ant-checkbox-input").check();
    await page.locator(".toolbar-right").getByRole("button", { name: /^删\s*除$/ }).click();
    await page.locator(".ant-popover").getByRole("button", { name: /确\s*定/ }).click();

    await expect.poll(() => deletedIds).toEqual(containers.map((c) => c.id));
    await expect(page.locator("text=web-1")).not.toBeVisible();
    await expect(page.locator("text=db-1")).not.toBeVisible();
  });
});
