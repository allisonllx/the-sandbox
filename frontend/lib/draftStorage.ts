export type SaveStatus =
  | "idle"
  | "unsaved"
  | "local"
  | "saved"
  | "offline"
  | "submitting";

export interface DraftRecord {
  files: Record<string, string>;
  updated_at: string;
  revision: number;
}

const DB_NAME = "sandbox-drafts";
const STORE_NAME = "drafts";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE_NAME);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function draftKey(challengeId: string, workspaceId: string): string {
  return `draft:${challengeId}:${workspaceId}`;
}

export async function loadLocalDraft(
  challengeId: string,
  workspaceId: string
): Promise<DraftRecord | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const req = tx.objectStore(STORE_NAME).get(draftKey(challengeId, workspaceId));
    req.onsuccess = () => resolve((req.result as DraftRecord | undefined) ?? null);
    req.onerror = () => reject(req.error);
  });
}

export async function saveLocalDraft(
  challengeId: string,
  workspaceId: string,
  record: DraftRecord
): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(record, draftKey(challengeId, workspaceId));
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export function pickNewerDraft(
  local: DraftRecord | null,
  server: DraftRecord | null
): DraftRecord | null {
  if (!local) return server;
  if (!server) return local;
  return new Date(local.updated_at) >= new Date(server.updated_at) ? local : server;
}
