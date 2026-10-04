"use client";

import { create } from "zustand";

export type ToastVariant = "default" | "success" | "error" | "loading";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: ToastItem[];
  push: (toast: Omit<ToastItem, "id">) => string;
  dismiss: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts.slice(-4), { ...toast, id }] }));
    if (toast.variant !== "loading") {
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, 4000);
    }
    return id;
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export function toast(title: string, opts?: { description?: string; variant?: ToastVariant }) {
  return useToastStore.getState().push({
    title,
    description: opts?.description,
    variant: opts?.variant ?? "default",
  });
}

export async function toastPromise<T>(
  promise: Promise<T>,
  messages: { loading: string; success: string; error?: string },
): Promise<T> {
  const id = toast(messages.loading, { variant: "loading" });
  try {
    const result = await promise;
    useToastStore.getState().dismiss(id);
    toast(messages.success, { variant: "success" });
    return result;
  } catch (e) {
    useToastStore.getState().dismiss(id);
    toast(messages.error ?? "Something went wrong", {
      variant: "error",
      description: e instanceof Error ? e.message : String(e),
    });
    throw e;
  }
}
