"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

export function readStoredSize(key: string, fallback: number) {
  if (typeof window === "undefined") return fallback;
  const raw = localStorage.getItem(key);
  const n = raw ? Number(raw) : NaN;
  return Number.isFinite(n) ? n : fallback;
}

function armDragSession(cursor: string, onMove: (ev: PointerEvent) => void, onEnd: () => void) {
  const previousCursor=document.body.style.cursor,previousSelect=document.body.style.userSelect;
  document.body.style.cursor = cursor;
  document.body.style.userSelect = "none";

  let ended=false;
  const onUp = () => {
    if(ended)return;
    ended=true;
    document.removeEventListener("pointermove", onMove);
    document.removeEventListener("pointerup", onUp);
    document.removeEventListener("pointercancel", onUp);
    window.removeEventListener("blur", onUp);
    document.body.style.cursor = previousCursor;
    document.body.style.userSelect = previousSelect;
    onEnd();
  };

  document.addEventListener("pointermove", onMove);
  document.addEventListener("pointerup", onUp);
  document.addEventListener("pointercancel", onUp);
  window.addEventListener("blur", onUp);
  return onUp;
}

export function useVerticalSplitResize({
  storageKey,
  defaultSize,
  minSize,
  minOtherSize,
  containerRef,
}: {
  storageKey: string;
  defaultSize: number;
  minSize: number;
  minOtherSize: number;
  containerRef: RefObject<HTMLElement | null>;
}) {
  const [size, setSize] = useState(() => readStoredSize(storageKey, defaultSize));

  const onResizePointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      const container = containerRef.current;
      if (!container) return;

      let latest = size;

      armDragSession(
        "ns-resize",
        (ev) => {
          const rect = container.getBoundingClientRect();
          const max = rect.height - minOtherSize;
          latest = Math.min(Math.max(ev.clientY - rect.top, minSize), max);
          setSize(latest);
        },
        () => {
          localStorage.setItem(storageKey, String(Math.round(latest)));
        },
      );
    },
    [containerRef, minOtherSize, minSize, size, storageKey],
  );

  return { size, onResizePointerDown };
}

export function useHorizontalPanelResize({
  storageKey,
  defaultSize,
  minSize,
  maxSize,
}: {
  storageKey: string;
  defaultSize: number;
  minSize: number;
  maxSize: number;
}) {
  const [size, setSize] = useState(() => readStoredSize(storageKey, defaultSize));
  const cleanup=useRef<(()=>void)|null>(null);
  useEffect(()=>()=>cleanup.current?.(),[]);

  const onResizePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if(e.button!==0)return;
      e.preventDefault();
      cleanup.current?.();
      const startX = e.clientX;
      const startW = size;
      let latest = startW;

      cleanup.current=armDragSession(
        "ew-resize",
        (ev) => {
          latest = Math.min(Math.max(startW + (startX - ev.clientX), minSize), maxSize);
          setSize(latest);
        },
        () => {
          localStorage.setItem(storageKey, String(Math.round(latest)));
        },
      );
    },
    [maxSize, minSize, size, storageKey],
  );

  return { size, onResizePointerDown };
}
