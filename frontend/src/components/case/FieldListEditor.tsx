interface FieldListEditorProps {
  id: string;
  label: string;
  value: string | null | undefined;
  onChange: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
}

export function FieldListEditor({
  id,
  label,
  value,
  onChange,
  placeholder,
  readOnly = false,
}: FieldListEditorProps) {
  return (
    <div className="form-field">
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <textarea
        id={id}
        className="textarea textarea--compact"
        value={value ?? ""}
        placeholder={placeholder}
        readOnly={readOnly}
        onChange={(event) => onChange(event.target.value)}
      />
      <div className="field-hint">One item per line</div>
    </div>
  );
}
