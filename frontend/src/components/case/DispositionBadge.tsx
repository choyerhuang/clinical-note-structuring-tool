import type { Disposition } from "../../types/case";

interface DispositionBadgeProps {
  disposition: Disposition | null;
}

export function DispositionBadge({ disposition }: DispositionBadgeProps) {
  if (!disposition) {
    return <span className="badge badge--muted">No disposition</span>;
  }

  return (
    <span className={`badge badge--disposition badge--disp-${disposition.toLowerCase()}`}>
      {disposition}
    </span>
  );
}
