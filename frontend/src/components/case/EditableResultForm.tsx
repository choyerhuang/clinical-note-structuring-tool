import type { ChangeEvent } from "react";

import type {
  Disposition,
  EditableResultFormValue,
} from "../../types/case";
import { FieldListEditor } from "./FieldListEditor";

const DISPOSITIONS: Disposition[] = ["Admit", "Observe", "Discharge", "Unknown"];

interface EditableResultFormProps {
  value: EditableResultFormValue;
  onChange: (value: EditableResultFormValue) => void;
  onSubmit: () => void;
  isSaving: boolean;
  editedFields: string[];
}

function EditedIndicator({ fieldName, editedFields }: { fieldName: string; editedFields: string[] }) {
  if (!editedFields.includes(fieldName)) {
    return null;
  }

  return <span className="badge badge--edited">Edited</span>;
}

export function EditableResultForm({
  value,
  onChange,
  onSubmit,
  isSaving,
  editedFields,
}: EditableResultFormProps) {
  const updateField = <K extends keyof EditableResultFormValue>(
    key: K,
    fieldValue: EditableResultFormValue[K],
  ) => {
    onChange({
      ...value,
      [key]: fieldValue,
    });
  };

  const onTextChange = (key: keyof EditableResultFormValue) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    updateField(key, event.target.value as EditableResultFormValue[keyof EditableResultFormValue]);
  };

  return (
    <div className="card">
      <div className="card__header">
        <div className="card__header-row">
          <h2 className="card__title">Final Review / Editable Version</h2>
          <span className="badge badge--user">User-editable</span>
        </div>
      </div>

      <div className="stack">
        <div className="form-field">
          <div className="field-label-row">
            <label htmlFor="chief_complaint_final" className="field-label">
              Chief Complaint
            </label>
            <EditedIndicator fieldName="chief_complaint_final" editedFields={editedFields} />
          </div>
          <input
            id="chief_complaint_final"
            className="input"
            value={value.chief_complaint_final}
            onChange={onTextChange("chief_complaint_final")}
          />
        </div>

        <div className="form-field">
          <div className="field-label-row">
            <label htmlFor="hpi_summary_final" className="field-label">
              HPI Summary
            </label>
            <EditedIndicator fieldName="hpi_summary_final" editedFields={editedFields} />
          </div>
          <textarea
            id="hpi_summary_final"
            className="textarea textarea--compact"
            value={value.hpi_summary_final}
            onChange={onTextChange("hpi_summary_final")}
          />
        </div>

        <div className="field-label-row">
          <span className="field-label">Key Findings</span>
          <EditedIndicator fieldName="key_findings_final" editedFields={editedFields} />
        </div>
        <FieldListEditor
          id="key_findings_final"
          label=""
          value={value.key_findings_final}
          onChange={(next) => updateField("key_findings_final", next)}
        />

        <div className="field-label-row">
          <span className="field-label">Suspected Conditions</span>
          <EditedIndicator fieldName="suspected_conditions_final" editedFields={editedFields} />
        </div>
        <FieldListEditor
          id="suspected_conditions_final"
          label=""
          value={value.suspected_conditions_final}
          onChange={(next) => updateField("suspected_conditions_final", next)}
        />

        <div className="form-field">
          <div className="field-label-row">
            <label htmlFor="disposition_final" className="field-label">
              Disposition
            </label>
            <EditedIndicator fieldName="disposition_final" editedFields={editedFields} />
          </div>
          <select
            id="disposition_final"
            className="select"
            value={value.disposition_final}
            onChange={(event) => updateField("disposition_final", event.target.value as Disposition)}
          >
            {DISPOSITIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className="field-label-row">
          <span className="field-label">Uncertainties</span>
          <EditedIndicator fieldName="uncertainties_final" editedFields={editedFields} />
        </div>
        <FieldListEditor
          id="uncertainties_final"
          label=""
          value={value.uncertainties_final}
          onChange={(next) => updateField("uncertainties_final", next)}
        />

        <div className="form-field">
          <div className="field-label-row">
            <label htmlFor="revised_hpi_final" className="field-label">
              Revised HPI
            </label>
            <EditedIndicator fieldName="revised_hpi_final" editedFields={editedFields} />
          </div>
          <textarea
            id="revised_hpi_final"
            className="textarea textarea--large"
            value={value.revised_hpi_final}
            onChange={onTextChange("revised_hpi_final")}
          />
        </div>

        <div className="button-row">
          <button className="button button--primary" onClick={onSubmit} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Final Result"}
          </button>
        </div>
      </div>
    </div>
  );
}
