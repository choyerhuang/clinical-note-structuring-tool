import type { ChangeEvent } from "react";

import type { NoteType } from "../../types/case";

interface NoteSourceSectionProps {
  id: string;
  title: string;
  value: string;
  onChange: (value: string) => void;
  noteType?: NoteType;
  onUpload?: (file: File, noteType: NoteType) => void;
  uploadState?: {
    isUploading: boolean;
    error: string | null;
    warning: string | null;
  };
  required?: boolean;
  placeholder?: string;
}

export function NoteSourceSection({
  id,
  title,
  value,
  onChange,
  noteType,
  onUpload,
  uploadState,
  required = false,
  placeholder,
}: NoteSourceSectionProps) {
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && noteType && onUpload) {
      onUpload(selectedFile, noteType);
    }
    event.target.value = "";
  };

  return (
    <div className="note-source-card">
      <div className="field-label-row">
        <label htmlFor={id} className="field-label">
          {title}
        </label>
        {noteType && onUpload ? (
          <label className="button button--secondary button--upload">
            {uploadState?.isUploading ? "Uploading..." : "Upload PDF or DOCX"}
            <input
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden-file-input"
              onChange={handleFileChange}
              disabled={uploadState?.isUploading}
            />
          </label>
        ) : null}
      </div>

      <textarea
        id={id}
        className="textarea textarea--large"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
      />

      {uploadState?.warning ? <div className="warning-box">{uploadState.warning}</div> : null}
      {uploadState?.error ? <div className="error-banner">{uploadState.error}</div> : null}
    </div>
  );
}
