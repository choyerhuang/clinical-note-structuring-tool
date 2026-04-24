export type CaseStatus = "draft" | "generated" | "saved";
export type Disposition = "Admit" | "Observe" | "Discharge" | "Unknown";
export type NoteType = "er" | "hp";

export interface GeneratedResult {
  id: number;
  chief_complaint_generated: string;
  hpi_summary_generated: string;
  key_findings_generated: string[];
  suspected_conditions_generated: string[];
  disposition_generated: Disposition;
  uncertainties_generated: string[];
  revised_hpi_generated: string;
  generation_warnings: string[];
  verification_result: Record<string, unknown> | null;
  mcg_result: Record<string, unknown> | null;
  confidence_result: {
    score?: number;
    level?: string;
    label?: string;
    factors?: Array<{
      type?: string;
      label?: string;
      impact?: number;
      details?: string[];
    }>;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface EditedResult {
  id: number;
  chief_complaint_final: string;
  hpi_summary_final: string;
  key_findings_final: string[];
  suspected_conditions_final: string[];
  disposition_final: Disposition;
  uncertainties_final: string[];
  revised_hpi_final: string;
  edited_fields: string[];
  last_edited_at: string;
}

export interface CaseSummary {
  id: number;
  title: string;
  original_note: string;
  status: CaseStatus;
  latest_disposition: Disposition | null;
  has_user_edits: boolean;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseSummary {
  generated_result: GeneratedResult | null;
  edited_result: EditedResult | null;
  generation_warnings?: string[];
  generation_warning_groups?: {
    missing_data: string[];
    potential_issues: string[];
  };
}

export interface CreateCasePayload {
  title: string;
  original_note: string;
}

export interface SaveEditedResultPayload {
  chief_complaint_final: string;
  hpi_summary_final: string;
  key_findings_final: string[];
  suspected_conditions_final: string[];
  disposition_final: Disposition;
  uncertainties_final: string[];
  revised_hpi_final: string;
}

export interface EditableResultFormValue {
  chief_complaint_final: string;
  hpi_summary_final: string;
  key_findings_final: string;
  suspected_conditions_final: string;
  disposition_final: Disposition;
  uncertainties_final: string;
  revised_hpi_final: string;
}

export interface ParseNoteResponse {
  success: boolean;
  text: string;
  warning: string | null;
  error: string | null;
}
