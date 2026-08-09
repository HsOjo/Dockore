import { test, expect } from "@playwright/test";

test.use({ storageState: "playwright/.auth/user.json" });

test.describe("Settings", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/health", async (route) => {
      await route.fulfill({ json: { status: "ok", version: process.env.DOCKORE_VERSION! } });
    });
    await page.route("**/api/auth/validate", async (route) => {
      await route.fulfill({ json: { valid: true } });
    });
  });

  test("displays settings form", async ({ page }) => {
    await page.route("**/api/settings", async (route, request) => {
      if (request.method() === "PUT") {
        return route.fulfill({ json: request.postDataJSON() });
      }
      await route.fulfill({ json: { docker_host: "unix:///var/run/docker.sock" } });
    });

    await page.goto("/settings");
    await expect(page.locator("text=界面设置")).toBeVisible();
    await expect(page.locator("text=后端设置")).toBeVisible();
    await expect(page.locator("text=服务器信息")).toBeVisible();
    await expect(page.getByPlaceholder("unix:///var/run/docker.sock")).toHaveValue(
      "unix:///var/run/docker.sock"
    );
    await expect(page.getByRole("button", { name: /^保\s*存$/ })).toBeVisible();
  });

  test("saves backend settings", async ({ page }) => {
    let putBody: { docker_host?: string | null } | null = null;
    await page.route("**/api/settings", async (route, request) => {
      if (request.method() === "PUT") {
        putBody = request.postDataJSON();
        return route.fulfill({ json: putBody });
      }
      await route.fulfill({ json: { docker_host: "unix:///var/run/docker.sock" } });
    });

    await page.goto("/settings");
    const input = page.getByPlaceholder("unix:///var/run/docker.sock");
    await input.fill("tcp://docker-proxy:2375");
    await page.getByRole("button", { name: /^保\s*存$/ }).click();

    await expect(page.locator("text=已保存")).toBeVisible();
    expect(putBody).toEqual({ docker_host: "tcp://docker-proxy:2375" });
  });
});
