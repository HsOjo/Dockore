import { test, expect } from "@playwright/test";

// UI settings exist (welcome flow done) but no server is configured.
test.use({
  storageState: {
    cookies: [],
    origins: [
      {
        origin: "http://localhost:1420",
        localStorage: [
          { name: "dockore_ui", value: JSON.stringify({ theme: "auto", locale: "zh-CN" }) },
        ],
      },
    ],
  },
});

test.describe("Routing", () => {
  test("redirects to onboarding when not connected", async ({ page }) => {
    await page.goto("/containers");
    await page.waitForURL("/onboarding");
    await expect(page).toHaveURL("/onboarding");
    await expect(page.getByText("连接服务器", { exact: true })).toBeVisible();
  });
});
