import { describe, expect, it } from "vitest";
import { localDateTimeToUtc, localDateTimeValue, sunAnglesFromEnu } from "./sun-study";

describe("sun study clock", () => {
  it("converts IANA local time to UTC without the machine timezone", () => {
    expect(localDateTimeToUtc("2026-06-21T12:00", "Asia/Kolkata")).toBe("2026-06-21T06:30:00.000Z");
    expect(localDateTimeValue("2026-06-21T06:30:00.000Z", "Asia/Kolkata")).toBe("2026-06-21T12:00");
  });
  it("rejects daylight-saving gaps and ambiguous times", () => {
    expect(() => localDateTimeToUtc("2026-02-30T12:00", "Asia/Kolkata")).toThrow("valid local date");
    expect(() => localDateTimeToUtc("2026-10-03T24:00", "Asia/Kolkata")).toThrow("valid local date");
    expect(() => localDateTimeToUtc("2026-03-08T02:30", "America/New_York")).toThrow("does not exist");
    expect(() => localDateTimeToUtc("2026-11-01T01:30", "America/New_York")).toThrow("ambiguous");
    expect(() => localDateTimeToUtc("2026-06-21T12:00", "Invalid/Zone")).toThrow();
  });
  it("reports cardinal azimuths and geometric daylight", () => {
    expect(sunAnglesFromEnu(1, 0, 0).azimuth).toBe(90);
    expect(sunAnglesFromEnu(0, 1, 0).azimuth).toBe(0);
    expect(sunAnglesFromEnu(0, 0, 1).elevation).toBe(90);
    expect(sunAnglesFromEnu(0, 1, -1).elevation).toBe(-45);
  });
});
