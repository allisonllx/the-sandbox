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
  deliverable_types?: DeliverableType[];
  evaluation_focus?: string[];
  created_at: string;
}

export interface RelaxResponse {
  item_id: string;
  preview: RelaxedPreview;
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
  brand_proxy?: string | null;
  deliverable_types?: DeliverableType[];
  evaluation_focus?: string[];
  microprd: MicroPRD;
  dataset_ready: boolean;
  starter_ready?: boolean;
  dataset_anomalies: string[];
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
