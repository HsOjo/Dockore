import { describe, it, expect, beforeEach } from "vitest";
import { sha256 } from "js-sha256";
import {
  setBaseURL,
  setAuthToken,
  getBaseURL,
  getAuthToken,
  createConfiguredClient,
  api,
} from "./index.js";

describe("api", () => {
  beforeEach(() => {
    setBaseURL("");
    setAuthToken("");
  });

  it("setBaseURL strips trailing slash", () => {
    setBaseURL("http://localhost:8000/");
    expect(getBaseURL()).toBe("http://localhost:8000");
  });

  it("setAuthToken stores raw token", () => {
    setAuthToken("my-token");
    expect(getAuthToken()).toBe("my-token");
  });

  it("createConfiguredClient returns an openapi-fetch client", () => {
    setBaseURL("http://localhost:8000");
    setAuthToken("t");
    const client = createConfiguredClient();
    expect(typeof client.GET).toBe("function");
    expect(typeof client.POST).toBe("function");
    expect(typeof client.DELETE).toBe("function");
  });

  it("module-level api singleton exposes typed methods", () => {
    expect(typeof api.GET).toBe("function");
  });

  it("auth header uses sha256 hex of the token", async () => {
    setBaseURL("http://localhost:8000");
    setAuthToken("secret");
    const client = createConfiguredClient();
    let captured: Request | undefined;
    const fetchImpl: typeof fetch = async (input: any) => {
      captured = input instanceof Request ? input : new Request(input);
      return new Response(JSON.stringify({ valid: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    await client.GET("/api/health", { fetch: fetchImpl } as any);
    expect(captured!.headers.get("Authorization")).toBe(`Bearer ${sha256("secret")}`);
  });

  it("omits auth header when token is empty", async () => {
    setBaseURL("http://localhost:8000");
    const client = createConfiguredClient();
    let captured: Request | undefined;
    const fetchImpl: typeof fetch = async (input: any) => {
      captured = input instanceof Request ? input : new Request(input);
      return new Response("{}", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };
    await client.GET("/api/health", { fetch: fetchImpl } as any);
    expect(captured!.headers.get("Authorization")).toBeNull();
  });
});
