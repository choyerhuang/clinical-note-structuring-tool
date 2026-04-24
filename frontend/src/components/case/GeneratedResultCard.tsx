import type { GeneratedResult } from "../../types/case";
import { EmptyState } from "./EmptyState";
import { WarningBox } from "./WarningBox";

interface GeneratedResultCardProps {
  result: GeneratedResult | null;
  warnings: string[];
  warningGroups?: {
    missing_data: string[];
    potential_issues: string[];
  };
  isGenerating: boolean;
  onGenerate: () => void;
}

function ReadOnlyList({ items }: { items: string[] }) {
  if (!items.length) {
    return <div className="field-readonly field-readonly--muted">No items</div>;
  }

  return (
    <ul className="tag-list">
      {items.map((item) => (
        <li key={item} className="tag-list__item">
          {item}
        </li>
      ))}
    </ul>
  );
}

function JsonBlock({
  value,
  emptyMessage,
}: {
  value: Record<string, unknown> | null;
  emptyMessage: string;
}) {
  if (!value) {
    return <div className="field-readonly field-readonly--muted">{emptyMessage}</div>;
  }

  return <pre className="note-block">{JSON.stringify(value, null, 2)}</pre>;
}

function ConfidenceBlock({
  confidence,
}: {
  confidence: GeneratedResult["confidence_result"];
}) {
  if (!confidence) {
    return (
      <div className="field-readonly field-readonly--muted">
        No confidence metadata available.
      </div>
    );
  }

  const percentage =
    typeof confidence.score === "number"
      ? `${Math.round(confidence.score * 100)}%`
      : "Unknown";

  return (
    <div className="stack">
      <div className="field-readonly">
        {(confidence.label ?? "Admission Support Confidence")}:{" "}
        {confidence.level ?? "Unknown"} ({percentage})
      </div>
      {confidence.factors?.length ? (
        <ul className="warning-box__list">
          {confidence.factors.map((factor, index) => (
            <li key={`${factor.label ?? "factor"}-${index}`}>
              {factor.label ?? "Unnamed factor"} ({typeof factor.impact === "number" ? `${factor.impact > 0 ? "+" : ""}${factor.impact.toFixed(2)}` : "n/a"})
              {factor.details?.length ? `: ${factor.details.join(", ")}` : ""}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function GeneratedResultCard({
  result,
  warnings,
  warningGroups,
  isGenerating,
  onGenerate,
}: GeneratedResultCardProps) {
  return (
    <div className="card">
      <div className="card__header">
        <div className="card__header-row">
          <h2 className="card__title">AI Generated Output</h2>
          <span className="badge badge--ai">AI-generated</span>
        </div>
      </div>

      {!result ? (
        <EmptyState
          title="No generated output yet"
          description="Run generation to create structured output and a draft Revised HPI."
          action={
            <button className="button button--primary" onClick={onGenerate} disabled={isGenerating}>
              {isGenerating ? "Generating..." : "Generate Structured Output"}
            </button>
          }
        />
      ) : (
        <div className="stack">
          <WarningBox warnings={warnings} warningGroups={warningGroups} />
          <div>
            <div className="field-label">Generation Insights</div>
            <div className="stack">
              <div>
                <div className="field-label">Admission Support Confidence</div>
                <ConfidenceBlock confidence={result.confidence_result} />
              </div>
              <div>
                <div className="field-label">Verification</div>
                <JsonBlock
                  value={result.verification_result}
                  emptyMessage="No verification metadata available."
                />
              </div>
              <div>
                <div className="field-label">Persisted Warnings</div>
                <ReadOnlyList
                  items={result.generation_warnings}
                />
              </div>
              <div>
                <div className="field-label">Criteria / MCG</div>
                <JsonBlock
                  value={result.mcg_result}
                  emptyMessage="No criteria metadata available."
                />
              </div>
            </div>
          </div>
          <div>
            <div className="field-label">Chief Complaint</div>
            <div className="field-readonly">{result.chief_complaint_generated || "Not available"}</div>
          </div>
          <div>
            <div className="field-label">HPI Summary</div>
            <div className="field-readonly">{result.hpi_summary_generated || "Not available"}</div>
          </div>
          <div>
            <div className="field-label">Key Findings</div>
            <ReadOnlyList items={result.key_findings_generated} />
          </div>
          <div>
            <div className="field-label">Suspected Conditions</div>
            <ReadOnlyList items={result.suspected_conditions_generated} />
          </div>
          <div>
            <div className="field-label">Disposition</div>
            <div className="field-readonly">{result.disposition_generated}</div>
          </div>
          <div>
            <div className="field-label">Uncertainties</div>
            <ReadOnlyList items={result.uncertainties_generated} />
          </div>
          <div>
            <div className="field-label">Revised HPI</div>
            <div className="field-readonly">{result.revised_hpi_generated || "Not available"}</div>
          </div>
          <div className="button-row">
            <button className="button button--secondary" onClick={onGenerate} disabled={isGenerating}>
              {isGenerating ? "Generating..." : "Regenerate"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
