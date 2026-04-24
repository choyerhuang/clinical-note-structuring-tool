import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";

import { deleteCase, generateCase, getCase, saveCase } from "../api/cases";
import { EditableResultForm } from "../components/case/EditableResultForm";
import { EmptyState } from "../components/case/EmptyState";
import { GeneratedResultCard } from "../components/case/GeneratedResultCard";
import { LoadingBlock } from "../components/case/LoadingBlock";
import { OriginalNoteCard } from "../components/case/OriginalNoteCard";
import type {
  CaseDetail,
  EditableResultFormValue,
  SaveEditedResultPayload,
} from "../types/case";

function normalizeMultilineText(value: string[] | string | null | undefined): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => item.trim())
      .filter((item) => item.length > 0)
      .join("\n");
  }

  return (value ?? "")
    .split("\n")
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
    .join("\n");
}

function parseMultilineText(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function buildSavePayload(formValue: EditableResultFormValue): SaveEditedResultPayload {
  return {
    chief_complaint_final: formValue.chief_complaint_final,
    hpi_summary_final: formValue.hpi_summary_final,
    key_findings_final: parseMultilineText(formValue.key_findings_final),
    suspected_conditions_final: parseMultilineText(formValue.suspected_conditions_final),
    disposition_final: formValue.disposition_final,
    uncertainties_final: parseMultilineText(formValue.uncertainties_final),
    revised_hpi_final: formValue.revised_hpi_final,
  };
}

function getInitialEditablePayload(caseData: CaseDetail): EditableResultFormValue {
  if (caseData.edited_result) {
    return {
      chief_complaint_final: caseData.edited_result.chief_complaint_final,
      hpi_summary_final: caseData.edited_result.hpi_summary_final,
      key_findings_final: normalizeMultilineText(caseData.edited_result.key_findings_final),
      suspected_conditions_final: normalizeMultilineText(
        caseData.edited_result.suspected_conditions_final,
      ),
      disposition_final: caseData.edited_result.disposition_final,
      uncertainties_final: normalizeMultilineText(caseData.edited_result.uncertainties_final),
      revised_hpi_final: caseData.edited_result.revised_hpi_final,
    };
  }

  if (caseData.generated_result) {
    return {
      chief_complaint_final: caseData.generated_result.chief_complaint_generated,
      hpi_summary_final: caseData.generated_result.hpi_summary_generated,
      key_findings_final: normalizeMultilineText(caseData.generated_result.key_findings_generated),
      suspected_conditions_final: normalizeMultilineText(
        caseData.generated_result.suspected_conditions_generated,
      ),
      disposition_final: caseData.generated_result.disposition_generated,
      uncertainties_final: normalizeMultilineText(caseData.generated_result.uncertainties_generated),
      revised_hpi_final: caseData.generated_result.revised_hpi_generated,
    };
  }

  return {
    chief_complaint_final: "",
    hpi_summary_final: "",
    key_findings_final: "",
    suspected_conditions_final: "",
    disposition_final: "Unknown",
    uncertainties_final: "",
    revised_hpi_final: "",
  };
}

function getEditedFields(caseData: CaseDetail, formState: EditableResultFormValue) {
  if (caseData.edited_result?.edited_fields.length) {
    return caseData.edited_result.edited_fields;
  }

  const source = caseData.generated_result;
  if (!source) {
    return [];
  }
  const normalizedSourceKeyFindings = normalizeMultilineText(source.key_findings_generated);
  const normalizedSourceSuspectedConditions = normalizeMultilineText(
    source.suspected_conditions_generated,
  );
  const normalizedSourceUncertainties = normalizeMultilineText(source.uncertainties_generated);

  const edited: string[] = [];
  if (formState.chief_complaint_final !== source.chief_complaint_generated) {
    edited.push("chief_complaint_final");
  }
  if (formState.hpi_summary_final !== source.hpi_summary_generated) {
    edited.push("hpi_summary_final");
  }
  if (formState.key_findings_final !== normalizedSourceKeyFindings) {
    edited.push("key_findings_final");
  }
  if (formState.suspected_conditions_final !== normalizedSourceSuspectedConditions) {
    edited.push("suspected_conditions_final");
  }
  if (formState.disposition_final !== source.disposition_generated) {
    edited.push("disposition_final");
  }
  if (formState.uncertainties_final !== normalizedSourceUncertainties) {
    edited.push("uncertainties_final");
  }
  if (formState.revised_hpi_final !== source.revised_hpi_generated) {
    edited.push("revised_hpi_final");
  }
  return edited;
}

export function CaseDetailPage() {
  const navigate = useNavigate();
  const params = useParams();
  const caseId = Number(params.id);

  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [editableData, setEditableData] = useState<EditableResultFormValue | null>(null);
  const [generationWarnings, setGenerationWarnings] = useState<string[]>([]);
  const [generationWarningGroups, setGenerationWarningGroups] = useState<
    CaseDetail["generation_warning_groups"]
  >();
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCase = async () => {
      if (!Number.isFinite(caseId)) {
        setError("Invalid case id.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const data = await getCase(caseId);
        setCaseData(data);
        setEditableData(getInitialEditablePayload(data));
        setGenerationWarnings(data.generation_warnings ?? data.generated_result?.generation_warnings ?? []);
        setGenerationWarningGroups(data.generation_warning_groups);
      } catch (err) {
        if (axios.isAxiosError(err)) {
          setError("Unable to load the case.");
        } else {
          setError("An unexpected error occurred while loading the case.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    void loadCase();
  }, [caseId]);

  const editedFields = useMemo(() => {
    if (!caseData || !editableData) {
      return [];
    }
    return getEditedFields(caseData, editableData);
  }, [caseData, editableData]);

  const handleGenerate = async () => {
    if (!caseData) {
      return;
    }

    setIsGenerating(true);
    setError(null);
    try {
      const updatedCase = await generateCase(caseData.id);
      setCaseData(updatedCase);
      setEditableData(getInitialEditablePayload(updatedCase));
      setGenerationWarnings(
        updatedCase.generation_warnings ?? updatedCase.generated_result?.generation_warnings ?? [],
      );
      setGenerationWarningGroups(updatedCase.generation_warning_groups);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? "Unable to generate structured output.");
      } else {
        setError("An unexpected error occurred during generation.");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!caseData || !editableData) {
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const updatedCase = await saveCase(caseData.id, buildSavePayload(editableData));
      setCaseData(updatedCase);
      setEditableData(getInitialEditablePayload(updatedCase));
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError("Unable to save the final result. Please review the fields and try again.");
      } else {
        setError("An unexpected error occurred while saving.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!caseData) {
      return;
    }

    const confirmed = window.confirm(`Delete case "${caseData.title}"?`);
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    try {
      await deleteCase(caseData.id);
      navigate("/cases");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError("Unable to delete this case.");
      } else {
        setError("An unexpected error occurred while deleting.");
      }
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return <LoadingBlock label="Loading case..." />;
  }

  if (error && !caseData) {
    return (
      <EmptyState
        title="Case unavailable"
        description={error}
        action={
          <Link to="/cases" className="button button--secondary button--link">
            Back to Cases
          </Link>
        }
      />
    );
  }

  if (!caseData || !editableData) {
    return null;
  }

  return (
    <div className="page-stack">
      <div className="page-toolbar">
        <div>
          <h1 className="page-title">{caseData.title}</h1>
          <p className="page-description">
            Review the original note, compare the generated output, and save the final edited version.
          </p>
        </div>
        <div className="button-row">
          <Link to="/cases" className="button button--secondary button--link">
            Back to Cases
          </Link>
          <button
            type="button"
            className="button button--danger"
            onClick={() => void handleDelete()}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete Case"}
          </button>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="detail-grid">
        <OriginalNoteCard caseData={caseData} />
        <GeneratedResultCard
          result={caseData.generated_result}
          warnings={generationWarnings}
          warningGroups={generationWarningGroups}
          isGenerating={isGenerating}
          onGenerate={handleGenerate}
        />
        <EditableResultForm
          value={editableData}
          onChange={setEditableData}
          onSubmit={handleSave}
          isSaving={isSaving}
          editedFields={editedFields}
        />
      </div>
    </div>
  );
}
