import type { InputFormat } from "./types";

export const UPLOAD_SESSION_KEY = "sandbox.upload.pending";

export interface PendingUpload {
  content: string;
  sourceLabel: string;
  format: InputFormat;
  kind: "description" | "logs";
  fileName?: string;
}

export function savePendingUpload(payload: PendingUpload): void {
  sessionStorage.setItem(UPLOAD_SESSION_KEY, JSON.stringify(payload));
}

export function loadPendingUpload(): PendingUpload | null {
  const raw = sessionStorage.getItem(UPLOAD_SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as PendingUpload;
  } catch {
    return null;
  }
}

export function clearPendingUpload(): void {
  sessionStorage.removeItem(UPLOAD_SESSION_KEY);
}

export const MAX_UPLOAD_CHARS = 20000;
export const MAX_UPLOAD_BYTES = 512 * 1024;
