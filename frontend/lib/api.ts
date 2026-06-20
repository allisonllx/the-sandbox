import type {
  BacklogItem,
  PublishedChallenge,
  RelaxationConfig,
  RelaxResponse,
  PublishResponse,
  SubmitResponse,
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

  listChallenges: (): Promise<PublishedChallenge[]> =>
    request("/sandbox/challenges"),

  getChallenge: (id: string): Promise<PublishedChallenge> =>
    request(`/sandbox/challenges/${id}`),

  downloadDataset: (id: string): Promise<Blob> =>
    fetch(`${BASE}/sandbox/challenges/${id}/dataset`).then((res) => {
      if (!res.ok) throw new Error(`Download failed: ${res.status}`);
      return res.blob();
    }),

  submitSolution: (
    challengeId: string,
    code: string,
    language = "python"
  ): Promise<SubmitResponse> =>
    request(`/sandbox/challenges/${challengeId}/submit`, {
      method: "POST",
      body: JSON.stringify({ code, language }),
    }),
};
