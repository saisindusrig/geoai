import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(n: number, currency = "INR") {
  if (n >= 1e7) return `${(n / 1e7).toFixed(2)} Cr ${currency}`;
  return `${n.toLocaleString(undefined, { maximumFractionDigits: 0 })} ${currency}`;
}

export function formatQty(n: number, unit: string) {
  return `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })} ${unit}`;
}
