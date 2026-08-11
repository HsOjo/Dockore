import { describe, it, expect, vi } from "vitest";
import { checkForUpdate } from "./updater.js";

vi.mock("@dockore/shared", () => ({
  api: {
    GET: vi.fn(),
  },
}));

function makeResponse(haveNew: boolean) {
  return {
    data: {
      current: __DOCKORE_VERSION__,
      latest: "v9.9.9",
      have_new: haveNew,
      name: "v9.9.9",
      tag_name: "v9.9.9",
      published_at: "2026-01-01 00:00:00",
      html_url: "https://github.com/HsOjo/Dockore/releases/tag/v9.9.9",
      body: "release notes",
      download_url: "https://github.com/HsOjo/Dockore/releases/download/v9.9.9/Dockore.zip",
      assets: [
        { name: "Dockore.zip", url: "https://github.com/HsOjo/Dockore/releases/download/v9.9.9/Dockore.zip" },
      ],
    },
    error: undefined,
  };
}

describe("checkForUpdate", () => {
  it("returns parsed result when a newer version exists", async () => {
    const { api } = await import("@dockore/shared");
    vi.mocked(api.GET).mockResolvedValue(makeResponse(true) as any);

    const result = await checkForUpdate();
    expect(api.GET).toHaveBeenCalledWith("/api/update");
    expect(result.haveNew).toBe(true);
    expect(result.latest).toBe("v9.9.9");
    expect(result.downloadUrl).toBe("https://github.com/HsOjo/Dockore/releases/download/v9.9.9/Dockore.zip");
    expect(result.assets).toEqual([
      { name: "Dockore.zip", url: "https://github.com/HsOjo/Dockore/releases/download/v9.9.9/Dockore.zip" },
    ]);
  });

  it("returns parsed result when already up to date", async () => {
    const { api } = await import("@dockore/shared");
    vi.mocked(api.GET).mockResolvedValue(makeResponse(false) as any);

    const result = await checkForUpdate();
    expect(result.haveNew).toBe(false);
  });

  it("throws when the backend returns an error", async () => {
    const { api } = await import("@dockore/shared");
    vi.mocked(api.GET).mockResolvedValue({ data: undefined, error: { message: "network error" } } as any);

    await expect(checkForUpdate()).rejects.toEqual({ message: "network error" });
  });
});
