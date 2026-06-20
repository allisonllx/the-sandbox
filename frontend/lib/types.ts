export type SensitivityTag = "red" | "yellow" | "green";
export type BacklogStatus = "pending" | "reviewing" | "approved" | "published";
export type InputFormat = "auto" | "json" | "csv" | "log" | "text";

export type ChallengeTrack =
  | "technical"
  | "product_feature"
  | "automation"
  | "ai_governance"
  | "strategy";

export type DeliverableType =
  | "code_repo"
  | "frontend_prototype"
  | "external_link"
  | "mixed";

export interface FieldMetadata {
  name: string;
  inferred_type: string;
  nullable: boolean;
  sample_count: number;
}

export interface EventFrequency {
  event_type: string;
  count: number;
}

export interface PIIDetection {
  pii_type: string;
  count: number;
}

export interface SanitizedMetadata {
  format_detected: InputFormat;
  fields: FieldMetadata[];
  nested_paths: string[];
  approximate_row_scale: number | null;
  event_type_frequencies: EventFrequency[];
  pii_detections: PIIDetection[];
  ner: {
    status: "not_run" | "skipped" | "completed_empty" | "completed";
    model_available: boolean;
    entity_counts: { entity_label: string; count: number }[];
  };
  /** @deprecated Prefer metadata.ner.entity_counts */
  ner_entity_counts: { entity_label: string; count: number }[];
  blocked_chunk_count: number;
  processing_notes: string[];
}

export interface TechScores {
  severity: number;
  friction: number;
  sensitivity: number;
  sensitivity_reason: string;
  suggested_title: string;
}

export interface RelaxationConfig {
  abstract_logic: boolean;
  synthesize_variables: boolean;
  noise_level: number;
  abstract_brand?: boolean;
  obfuscate_domain?: boolean;
}

export interface DomainObfuscationPreview {
  domain_proxy: string;
  public_title: string;
  public_narrative: string;
  internal_intent: string;
  transform_rationale: string;
  brand_proxy: string;
  field_map?: Record<string, string>;
  public_fields?: string[];
}

export interface CompanyTechProfile {
  stage: string;
  team_size_range: string;
  tech_stack: string[];
  industry_broad?: string | null;
  verification_status: "verified" | "pending";
  verification_label: string;
}

export interface PublishDraft {
  title: string;
  context: string;
  definition_of_success: string[];
  structural_constraints: string[];
  evaluation_focus: string[];
  company_profile: CompanyTechProfile;
  user_persona?: string | null;
  problem_framing?: string | null;
  design_considerations?: string[];
  stack_guidance?: string[];
  deliverable_requirements?: string[];
}

export type RewardType = "cash_bounty" | "interview_pass";

export interface ChallengeReward {
  reward_type: RewardType;
  amount_usd?: number | null;
  interview_benchmark?: number;
  locked: boolean;
}

export interface ScopeCheckResponse {
  allowed: boolean;
  estimated_hours: number;
  reason: string;
  suggested_breakdown: string[];
}

export interface RelaxedPreview {
  original_fields: string[];
  relaxed_fields: string[];
  original_row_scale: number | null;
  relaxed_row_scale: number | null;
  noise_applied: number;
  variable_map: Record<string, string>;
}

export interface MicroPRD {
  challenge_id: string;
  title: string;
  track?: ChallengeTrack;
  brand_proxy?: string | null;
  context: string;
  definition_of_success: string[];
  structural_constraints: string[];
  sandbox_instructions: string[];
  user_persona?: string | null;
  problem_framing?: string | null;
  design_considerations?: string[];
  stack_guidance?: string[];
  deliverable_requirements?: string[];
  generated_at: string;
}

export interface BacklogItem {
  id: string;
  source_label: string;
  metadata: SanitizedMetadata;
  scores: TechScores | null;
  tag: SensitivityTag | null;
  status: BacklogStatus;
  relaxation_config: RelaxationConfig;
  relaxed_preview: RelaxedPreview | null;
  microprd: MicroPRD | null;
  track?: ChallengeTrack | null;
  suggested_track?: ChallengeTrack | null;
  brand_proxy?: string | null;
  company_profile?: CompanyTechProfile | null;
  publish_draft?: PublishDraft | null;
  deliverable_types?: DeliverableType[];
  evaluation_focus?: string[];
  sponsor_profile?: string | null;
  domain_preview?: DomainObfuscationPreview | null;
  reward?: ChallengeReward | null;
  pool_label?: string | null;
  created_at: string;
}

export interface RelaxResponse {
  item_id: string;
  preview: RelaxedPreview;
  domain_preview?: DomainObfuscationPreview | null;
  company_profile?: CompanyTechProfile | null;
  challenge_draft?: PublishDraft | null;
  scope_check?: ScopeCheckResponse | null;
}

export interface PublishResponse {
  item_id: string;
  microprd: MicroPRD;
  status: BacklogStatus;
  track?: ChallengeTrack;
  brand_proxy?: string | null;
}

export interface PublishedChallenge {
  id: string;
  title: string;
  status: string;
  track?: ChallengeTrack;
  company_profile: CompanyTechProfile;
  deliverable_types?: DeliverableType[];
  evaluation_focus?: string[];
  microprd: MicroPRD;
  dataset_ready: boolean;
  starter_ready?: boolean;
  dataset_anomalies: string[];
  reward?: ChallengeReward | null;
  reward_escrow_label?: string | null;
  published_at: string | null;
}

export interface StarterResponse {
  ok: boolean;
  challenge_id: string;
  files: Record<string, string>;
}

export interface WorkspaceBootstrapResponse {
  ok: boolean;
  workspace_id: string;
  draft: {
    files: Record<string, string>;
    client_revision: number;
    updated_at: string;
    server_updated_at?: string | null;
  } | null;
}

export interface Diagnostic {
  line: number;
  column: number;
  message: string;
  severity: string;
}

export interface JobStatusResponse {
  ok: boolean;
  job_id: string;
  status: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface Scorecard {
  track?: string;
  dimensions: Record<string, number>;
  summary: string;
  notes?: string[];
  execution_points?: number;
  interview_pass_earned?: boolean;
  interview_benchmark?: number;
}

export interface LeaderboardEntry {
  rank: number;
  display_name: string;
  track: ChallengeTrack;
  execution_points: number;
  highlight: string;
  challenge_id?: string | null;
}

export interface SponsorMatchEntry {
  rank: number;
  candidate_id: string;
  track: ChallengeTrack;
  execution_points: number;
  summary: string;
  submitted_at?: string | null;
}

export interface SponsorMatchesResponse {
  ok: boolean;
  challenge_id: string;
  challenge_title?: string | null;
  source: "live" | "demo" | "empty";
  entries: SponsorMatchEntry[];
}

export interface EnterpriseRadarEntry {
  rank_label: string;
  candidate_id: string;
  track: ChallengeTrack;
  execution_points: number;
  platform_signal: string;
}

export interface EnterpriseRadarResponse {
  ok: boolean;
  tier: string;
  entries: EnterpriseRadarEntry[];
}

export interface SubmitResponse {
  ok: boolean;
  submission_id: string;
  challenge_id: string;
  status: "received" | "queued_for_assessment" | "assessed";
  message: string;
  scorecard?: Scorecard | null;
}

export interface ScorecardResponse {
  ok: boolean;
  submission_id: string;
  track: ChallengeTrack;
  dimensions: Record<string, number>;
  summary: string;
  notes: string[];
}
