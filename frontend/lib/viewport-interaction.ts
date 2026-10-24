export type SelectionOperation = "replace" | "add" | "remove" | "toggle";
export function selectionOperation(current: string[], picked: string[], operation: SelectionOperation) {
  const unique = [...new Set(picked)];
  if (operation === "replace") return unique;
  if (operation === "remove") return current.filter(id => !unique.includes(id));
  if (operation === "toggle") return [...current.filter(id => !unique.includes(id)), ...unique.filter(id => !current.includes(id))];
  return [...new Set([...current, ...unique])];
}
export function dragStarted(x: number, y: number, startX: number, startY: number) {
  return Math.hypot(x - startX, y - startY) >= 5;
}
export function intersectsRectangle(a: { x: number; y: number; width: number; height: number }, b: typeof a) {
  return a.x <= b.x + b.width && a.x + a.width >= b.x && a.y <= b.y + b.height && a.y + a.height >= b.y;
}
export function numericTransformValue(text: string, mode: string): number | null {
  if (!/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(text)) return null;
  const value = Number(text);
  return Number.isFinite(value) && (mode !== "scale" || value > 0) ? value : null;
}
