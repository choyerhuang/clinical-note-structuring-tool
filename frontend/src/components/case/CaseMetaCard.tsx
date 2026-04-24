import { DispositionBadge } from "./DispositionBadge";
import { StatusBadge } from "./StatusBadge";
import type { CaseDetail } from "../../types/case";

interface CaseMetaCardProps {
  caseData: CaseDetail;
}

export function CaseMetaCard({ caseData }: CaseMetaCardProps) {
  return (
    <div className="card">
      <div className="card__header">
        <h3 className="card__title">Case Metadata</h3>
      </div>
      <div className="meta-grid">
        <div className="meta-item">
          <span className="meta-item__label">Status</span>
          <StatusBadge status={caseData.status} />
        </div>
        <div className="meta-item">
          <span className="meta-item__label">Latest Disposition</span>
          <DispositionBadge disposition={caseData.latest_disposition} />
        </div>
        <div className="meta-item">
          <span className="meta-item__label">User Edits</span>
          <span className="meta-item__value">
            {caseData.has_user_edits ? "Yes" : "No"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-item__label">Updated</span>
          <span className="meta-item__value">
            {new Date(caseData.updated_at).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}
