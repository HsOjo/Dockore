import { describe, it, expect } from "vitest";
import { containerStatusBadge, shortId, imageDisplayName } from "./text.js";

describe("utils/text", () => {
  it("containerStatusBadge maps statuses", () => {
    expect(containerStatusBadge("running")).toBe("processing");
    expect(containerStatusBadge("paused")).toBe("warning");
    expect(containerStatusBadge("dead")).toBe("error");
    expect(containerStatusBadge("exited")).toBe("default");
    expect(containerStatusBadge("unknown")).toBe("default");
  });

  it("shortId strips sha256 prefix and truncates", () => {
    expect(shortId("sha256:abcdef0123456789")).toBe("abcdef012345");
    expect(shortId("short")).toBe("short");
    expect(shortId("")).toBe("");
    expect(shortId(null)).toBe("");
  });

  it("imageDisplayName prefers tags", () => {
    expect(imageDisplayName({ id: "sha256:abcdef0123456789", tags: [] })).toBe("abcdef012345");
    expect(imageDisplayName({ id: "x", tags: ["nginx:latest", "nginx:1.25"] })).toBe("nginx:latest, nginx:1.25");
    expect(imageDisplayName(null)).toBe("");
  });
});
