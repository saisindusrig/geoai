export function localDateTimeToUtc(value: string, timeZone: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value);
  if (!match) throw new Error("Enter a valid local date and time.");
  const [, year, month, day, hour, minute] = match.map(Number);
  const local = Date.UTC(year, month - 1, day, hour, minute);
  if (!Number.isFinite(local) || new Date(local).toISOString().slice(0, 16) !== value) {
    throw new Error("Enter a valid local date and time.");
  }
  const format = new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  const asLocal = (utc: number) => {
    const parts = Object.fromEntries(format.formatToParts(new Date(utc)).map((p) => [p.type, p.value]));
    return Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour), Number(parts.minute));
  };
  let candidate = local;
  for (let i = 0; i < 4; i++) candidate += local - asLocal(candidate);
  if (asLocal(candidate) !== local) throw new Error("This local time does not exist in the selected timezone.");
  if (asLocal(candidate - 3600000) === local || asLocal(candidate + 3600000) === local) throw new Error("This local time is ambiguous. Enter an explicit UTC time.");
  return new Date(candidate).toISOString();
}

export function localDateTimeValue(utc: string, timeZone: string): string {
  const format = new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  const p = Object.fromEntries(format.formatToParts(new Date(utc)).map((part) => [part.type, part.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}

export function sunAnglesFromEnu(east: number, north: number, up: number) {
  return { azimuth: ((Math.atan2(east, north) * 180 / Math.PI) + 360) % 360,
    elevation: Math.atan2(up, Math.hypot(east, north)) * 180 / Math.PI };
}

export type ScenePreset = "ENGINEERING" | "REALISTIC" | "SUN_STUDY" | "SURVEY_QA";
export type SceneQuality = "PERFORMANCE" | "BALANCED" | "HIGH_DETAIL";
export type ShadowQuality = "OFF" | "BALANCED" | "HIGH";
export interface EngineeringMapPreferences { preset: ScenePreset; quality: SceneQuality; shadows: ShadowQuality; utc: string; timeZone: string }

export function scenePresetPreferences(current: EngineeringMapPreferences, preset: ScenePreset): EngineeringMapPreferences {
  return { ...current, preset, shadows: preset === "ENGINEERING" || preset === "SURVEY_QA" ? "OFF" : current.shadows === "OFF" ? "BALANCED" : current.shadows };
}
