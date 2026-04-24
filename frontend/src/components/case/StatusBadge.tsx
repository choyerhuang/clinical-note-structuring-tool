import type { CaseStatus } from "../../types/case";

interface StatusBadgeProps {
  status: CaseStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`badge badge--status badge--${status}`}>{status}</span>;
}
