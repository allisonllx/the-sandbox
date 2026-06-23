/** Browser workspace file rules — mirrors spec `student_may_add` (src/helpers/*.py). */

export const HELPER_DIR = "src/helpers";

export const HELPER_FILE_PATTERN = /^src\/helpers\/[a-zA-Z][a-zA-Z0-9_]*\.py$/;

export const HELPER_FILE_TEMPLATE = `"""Optional helper module — keep minimal."""

from __future__ import annotations

# Shared helpers only. Prefer implementing logic in the primary edit target.
`;

export const WORKSPACE_FILE_HINT =
  "New files go under src/helpers/ — one small helper is usually enough.";

export const WORKSPACE_LIMITS_NOTE =
  "No shell. Run Public Tests = pytest only.";

/** Turn VS Code-style input (utils.py or src/helpers/utils.py) into a full path. */
export function resolveNewFilePath(input: string): { path: string | null; error: string | null } {
  let trimmed = input.trim().replace(/^\/+/, "");
  if (!trimmed) {
    return { path: null, error: "Type a filename (e.g. utils.py)." };
  }
  if (trimmed.includes("..")) {
    return { path: null, error: "Path must not contain .." };
  }
  if (!trimmed.includes("/")) {
    trimmed = `${HELPER_DIR}/${trimmed}`;
  }
  const err = helperPathError(trimmed);
  if (err) {
    return { path: null, error: err };
  }
  const path = normalizeHelperPath(trimmed);
  if (!path) {
    return { path: null, error: "Invalid path." };
  }
  return { path, error: null };
}

export function normalizeHelperPath(input: string): string | null {
  const trimmed = input.trim().replace(/^\/+/, "");
  if (!HELPER_FILE_PATTERN.test(trimmed)) {
    return null;
  }
  return trimmed;
}

export function helperPathError(input: string): string | null {
  const trimmed = input.trim().replace(/^\/+/, "");
  if (!trimmed) return "Enter a file path.";
  if (trimmed.includes("..")) return "Path must not contain ..";
  if (!trimmed.startsWith(`${HELPER_DIR}/`)) {
    return `New files must live under ${HELPER_DIR}/ (e.g. utils.py → ${HELPER_DIR}/utils.py).`;
  }
  if (!trimmed.endsWith(".py")) return "Helper files must end with .py";
  if (!HELPER_FILE_PATTERN.test(trimmed)) {
    return "Use letters, numbers, and underscores in the filename.";
  }
  return null;
}

export function isUserAddedHelper(path: string): boolean {
  return HELPER_FILE_PATTERN.test(path);
}
