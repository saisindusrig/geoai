import { describe, it, expect } from "vitest";
import { BRAND_NAME, ASSISTANT_NAME, BRAND_TAGLINE, SITE_TITLE, publicSiteUrl } from "./brand";
import manifest from "../app/manifest";

describe("public branding and origin isolation", () => {
  it("uses the approved identity and local manifest start path", () => {
    expect(BRAND_NAME).toBe("StruvoCivil");
    expect(ASSISTANT_NAME).toBe("StruvoCivil Assistant");
    expect(BRAND_TAGLINE).toBe("Model. Analyze. Design.");
    expect(SITE_TITLE).toBe("StruvoCivil — Structural Engineering Software");
    expect(manifest()).toMatchObject({ name: BRAND_NAME, start_url: "/" });
  });
  it("supports a local metadata origin and rejects unsafe origins", () => {
    expect(publicSiteUrl("http://localhost:3001/path").href).toBe("http://localhost:3001/");
    expect(publicSiteUrl("https://struvocivil.com").origin).toBe("https://struvocivil.com");
    expect(() => publicSiteUrl("javascript:alert(1)")).toThrow();
    expect(() => publicSiteUrl("https://user:pass@example.com")).toThrow();
  });
});
