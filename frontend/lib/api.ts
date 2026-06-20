import type {
  BacklogItem,
  RelaxationConfig,
  RelaxResponse,
  PublishResponse,
} from "./types";

const BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getBacklog: (): Promise<BacklogItem[]> =>
    request("/triage/backlog"),

  getItem: (id: string): Promise<BacklogItem> =>
    request(`/triage/backlog/${id}`),

  relax: (itemId: string, config: RelaxationConfig): Promise<RelaxResponse> =>
    request(`/triage/relax/${itemId}`, {
      method: "POST",
      body: JSON.stringify({ config }),
    }),

  publish: (itemId: string, config: RelaxationConfig): Promise<PublishResponse> =>
    request(`/triage/publish/${itemId}`, {
      method: "POST",
      body: JSON.stringify({ config }),
    }),
};
