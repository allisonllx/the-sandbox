import type {
  BacklogItem,
  ChallengeReward,
  ChallengeTrack,
  Diagnostic,
  JobStatusResponse,
  LeaderboardEntry,
  EnterpriseRadarResponse,
  SponsorMatchesResponse,
  PublishedChallenge,
  IntakeResponse,
  PublishDraft,
  RelaxationConfig,
  RelaxResponse,
  PublishResponse,
  ScorecardResponse,
  StarterResponse,
  SubmitResponse,
  WorkspaceBootstrapResponse,
} from "./types";

const BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
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

  intake: (problemStatement: string, sourceLabel = "Founder brief"): Promise<IntakeResponse> =>
    request("/triage/intake", {
      method: "POST",
      body: JSON.stringify({
        problem_statement: problemStatement,
        source_label: sourceLabel,
        format: "text",
      }),
    }),

  relax: (
    itemId: string,
    config: RelaxationConfig,
    reward?: ChallengeReward,
    track?: ChallengeTrack,
    draft?: PublishDraft
  ): Promise<RelaxResponse> =>
    request(`/triage/relax/${itemId}`, {
      method: "POST",
      body: JSON.stringify({ config, reward, track, draft }),
    }),

  publish: (
    itemId: string,
    config: RelaxationConfig,
    reward?: ChallengeReward,
    track?: ChallengeTrack,
    draft?: PublishDraft
  ): Promise<PublishResponse> =>
    request(`/triage/publish/${itemId}`, {
      method: "POST",
      body: JSON.stringify({ config, reward, track, draft }),
    }),

  listChallenges: (track?: ChallengeTrack): Promise<PublishedChallenge[]> =>
    request(track ? `/sandbox/challenges?track=${track}` : "/sandbox/challenges"),

  getChallenge: (id: string): Promise<PublishedChallenge> =>
    request(`/sandbox/challenges/${id}`),

  getStarter: (id: string): Promise<StarterResponse> =>
    request(`/sandbox/challenges/${id}/starter`),

  bootstrapWorkspace: (id: string): Promise<WorkspaceBootstrapResponse> =>
    request(`/sandbox/challenges/${id}/workspace`),

  saveDraft: (
    challengeId: string,
    files: Record<string, string>,
    clientRevision: number,
    updatedAt: string
  ): Promise<{ ok: boolean; saved_at: string; revision: number }> =>
    request(`/sandbox/challenges/${challengeId}/draft`, {
      method: "PUT",
      body: JSON.stringify({
        files,
        client_revision: clientRevision,
        updated_at: updatedAt,
      }),
    }),

  validateFile: (path: string, content: string): Promise<{ diagnostics: Diagnostic[] }> =>
    request("/sandbox/validate", {
      method: "POST",
      body: JSON.stringify({ path, content }),
    }),

  runPublicTests: (
    challengeId: string,
    files: Record<string, string>
  ): Promise<{ job_id: string; status: string }> =>
    request(`/sandbox/challenges/${challengeId}/run`, {
      method: "POST",
      body: JSON.stringify({ files }),
    }),

  getJob: (jobId: string): Promise<JobStatusResponse> =>
    request(`/sandbox/jobs/${jobId}`),

  downloadDataset: (id: string): Promise<Blob> =>
    fetch(`${BASE}/sandbox/challenges/${id}/dataset`, { credentials: "include" }).then(
      (res) => {
        if (!res.ok) throw new Error(`Download failed: ${res.status}`);
        return res.blob();
      }
    ),

  downloadStarterZip: (id: string): Promise<Blob> =>
    fetch(`${BASE}/sandbox/challenges/${id}/starter/download`, {
      credentials: "include",
    }).then((res) => {
      if (!res.ok) throw new Error(`Starter download failed: ${res.status}`);
      return res.blob();
    }),

  submitSolution: (
    challengeId: string,
    files: Record<string, string>,
    language = "python",
    links?: Record<string, string>
  ): Promise<SubmitResponse> =>
    request(`/sandbox/challenges/${challengeId}/submit`, {
      method: "POST",
      body: JSON.stringify({ mode: "inline", files, language, links }),
    }),

  getScorecard: (submissionId: string): Promise<ScorecardResponse> =>
    request(`/sandbox/submissions/${submissionId}/scorecard`),

  getLeaderboard: (): Promise<{ ok: boolean; entries: LeaderboardEntry[] }> =>
    request("/sandbox/leaderboard"),

  getEnterpriseRadar: (): Promise<EnterpriseRadarResponse> =>
    request("/sandbox/enterprise/radar"),

  getSponsorMatches: (itemId: string): Promise<SponsorMatchesResponse> =>
    request(`/triage/backlog/${itemId}/matches`),

  submitZip: (challengeId: string, zipBytes: ArrayBuffer): Promise<SubmitResponse> =>
    fetch(`${BASE}/sandbox/challenges/${challengeId}/submit/zip`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/zip" },
      body: zipBytes,
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`API ${res.status}: ${body}`);
      }
      return res.json() as Promise<SubmitResponse>;
    }),
};
