import { CaseMetaCard } from "./CaseMetaCard";
import type { CaseDetail } from "../../types/case";

interface OriginalNoteCardProps {
  caseData: CaseDetail;
}

export function OriginalNoteCard({ caseData }: OriginalNoteCardProps) {
  return (
    <div className="column-stack">
      <div className="card">
        <div className="card__header">
          <h2 className="card__title">Original Note</h2>
        </div>
        <div className="stack">
          <div>
            <div className="field-label">Title</div>
            <div className="field-readonly">{caseData.title}</div>
          </div>
          <div>
            <div className="field-label">Original Clinical Note</div>
            <pre className="note-block">{caseData.original_note}</pre>
          </div>
        </div>
      </div>
      <CaseMetaCard caseData={caseData} />
    </div>
  );
}
