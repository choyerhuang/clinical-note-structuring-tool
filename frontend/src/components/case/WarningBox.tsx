interface WarningBoxProps {
  warnings: string[];
  warningGroups?: {
    missing_data: string[];
    potential_issues: string[];
  };
}

export function WarningBox({ warnings, warningGroups }: WarningBoxProps) {
  const missingData = warningGroups?.missing_data ?? [];
  const potentialIssues = warningGroups?.potential_issues ?? [];

  if (!warnings.length && !missingData.length && !potentialIssues.length) {
    return null;
  }

  return (
    <div className="warning-box">
      <div className="warning-box__title">Generation Warnings</div>
      {missingData.length ? (
        <div>
          <div className="field-label">Missing data</div>
          <ul className="warning-box__list">
            {missingData.map((warning) => (
              <li key={`missing-${warning}`}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {potentialIssues.length ? (
        <div>
          <div className="field-label">Potential issues</div>
          <ul className="warning-box__list">
            {potentialIssues.map((warning) => (
              <li key={`issue-${warning}`}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {!missingData.length && !potentialIssues.length ? (
        <ul className="warning-box__list">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
