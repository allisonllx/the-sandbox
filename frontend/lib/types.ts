export type SensitivityTag = "red" | "yellow" | "green";
export type BacklogStatus = "pending" | "reviewing" | "approved" | "published";
export type InputFormat = "auto" | "json" | "csv" | "log" | "text";

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
  context: string;
  definition_of_success: string[];
  structural_constraints: string[];
  sandbox_instructions: string[];
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
}
