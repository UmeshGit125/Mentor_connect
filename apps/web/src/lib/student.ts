"use client";
import { useSyncExternalStore } from "react";
import type { Student } from "@/lib/types";

// Student identity lives in localStorage; every access is guarded because
// storage can throw (private windows, blocked cookies).
const KEY = "mc_student";
const listeners = new Set<() => void>();
let cachedRaw: string | null | undefined;
let cachedValue: Student | null = null;

function readRaw(): string | null {
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function getSnapshot(): Student | null {
  const raw = readRaw();
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    try {
      cachedValue = raw ? (JSON.parse(raw) as Student) : null;
    } catch {
      cachedValue = null;
    }
  }
  return cachedValue;
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  window.addEventListener("storage", cb);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", cb);
  };
}

export function saveStudent(student: Student | null) {
  try {
    if (student) window.localStorage.setItem(KEY, JSON.stringify(student));
    else window.localStorage.removeItem(KEY);
  } catch {
    // Storage unavailable: keep the session in memory only.
    cachedRaw = undefined;
    cachedValue = student;
  }
  listeners.forEach((l) => l());
}

export function getStudentId(): string | null {
  return getSnapshot()?.id ?? null;
}

/** Returns the signed-in student, or null. `ready` is false during hydration. */
export function useStudent(): { student: Student | null; ready: boolean } {
  const student = useSyncExternalStore(subscribe, getSnapshot, () => null);
  const ready = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
  return { student, ready };
}
