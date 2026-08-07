import { test as setup, expect } from "@playwright/test";

const authFile = "playwright/.auth/user.json";

setup("authenticate", async ({ page }) => {
  // Mock health check, token validation and settings APIs
  await page.route("**/api/health", async (route) => {
    await route.fulfill({ json: { status: "ok", version: process.env.DOCKORE_VERSION! } });
  });
  await page.route("**/api/auth/validate", async (route) => {
    await route.fulfill({ json: { valid: true } });
  });
  await page.route("**/api/settings", async (route) => {
    await route.fulfill({ json: { docker_host: "unix:///var/run/docker.sock" } });
  });

  await page.goto("/onboarding");

  // Simulate an already-initialized client so the onboarding flow jumps
  // straight to the connection step. The connection config is saved after login.
  await page.evaluate(() => {
    localStorage.setItem("dockore_ui", JSON.stringify({ theme: "auto", locale: "zh-CN" }));
  });
  await page.reload();

  await page.getByPlaceholder(/服务器地址|Server URL/).fill("http://localhost:8000");
  await page.getByPlaceholder(/访问令牌|Access Token/).fill("test-token");
  await page.getByRole("button", { name: /^连\s*接$|^Connect$/ }).click();

  await page.waitForURL(/\/containers/);
  await expect(page).toHaveURL(/\/containers/);

  await page.context().storageState({ path: authFile });
});
