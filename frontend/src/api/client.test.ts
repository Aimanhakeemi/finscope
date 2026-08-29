import { afterEach, describe, expect, it, vi } from "vitest";
import { getHealth } from "./client";

afterEach(() => vi.restoreAllMocks());

describe("getHealth", () => {
  it("returns the health response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok", version: "0.1.0", llm_enabled: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    await expect(getHealth()).resolves.toEqual({
      status: "ok",
      version: "0.1.0",
      llm_enabled: false,
    });
    expect(fetch).toHaveBeenCalledWith("http://localhost:8000/healthz");
  });

  it("raises on an API error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 503 })));
    await expect(getHealth()).rejects.toThrow("API request failed: 503");
  });
});
