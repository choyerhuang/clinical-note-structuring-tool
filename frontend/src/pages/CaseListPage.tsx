import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

import { deleteCase, listCases } from "../api/cases";
import { DispositionBadge } from "../components/case/DispositionBadge";
import { EmptyState } from "../components/case/EmptyState";
import { LoadingBlock } from "../components/case/LoadingBlock";
import { StatusBadge } from "../components/case/StatusBadge";
import type { CaseSummary } from "../types/case";

export function CaseListPage() {
  const navigate = useNavigate();
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingCaseId, setDeletingCaseId] = useState<number | null>(null);

  useEffect(() => {
    const loadCases = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await listCases();
        setCases(data);
      } catch (err) {
        if (axios.isAxiosError(err)) {
          setError("Unable to load saved cases right now.");
        } else {
          setError("An unexpected error occurred while loading cases.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    void loadCases();
  }, []);

  const handleDelete = async (caseItem: CaseSummary) => {
    const confirmed = window.confirm(`Delete case "${caseItem.title}"?`);
    if (!confirmed) {
      return;
    }

    setDeletingCaseId(caseItem.id);
    setError(null);
    try {
      await deleteCase(caseItem.id);
      setCases((current) => current.filter((item) => item.id !== caseItem.id));
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError("Unable to delete the selected case.");
      } else {
        setError("An unexpected error occurred while deleting the case.");
      }
    } finally {
      setDeletingCaseId(null);
    }
  };

  return (
    <div className="page-stack">
      <div className="page-toolbar">
        <div>
          <h1 className="page-title">Saved Cases</h1>
          <p className="page-description">Review, reopen, and continue existing cases.</p>
        </div>
        <Link to="/cases/new" className="button button--primary button--link">
          New Case
        </Link>
      </div>

      {isLoading ? <LoadingBlock label="Loading saved cases..." /> : null}
      {error ? <div className="error-banner">{error}</div> : null}

      {!isLoading && !error && cases.length === 0 ? (
        <EmptyState
          title="No saved cases yet"
          description="Create your first case to begin the structuring workflow."
          action={
            <Link to="/cases/new" className="button button--primary button--link">
              Create New Case
            </Link>
          }
        />
      ) : null}

      {!isLoading && !error && cases.length > 0 ? (
        <div className="card table-card">
          <table className="case-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Latest Disposition</th>
                <th>User Edits</th>
                <th>Updated At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((caseItem) => (
                <tr key={caseItem.id} onClick={() => navigate(`/cases/${caseItem.id}`)}>
                  <td>{caseItem.title}</td>
                  <td>
                    <StatusBadge status={caseItem.status} />
                  </td>
                  <td>
                    <DispositionBadge disposition={caseItem.latest_disposition} />
                  </td>
                  <td>{caseItem.has_user_edits ? "Yes" : "No"}</td>
                  <td>{new Date(caseItem.updated_at).toLocaleString()}</td>
                  <td>
                    <button
                      type="button"
                      className="button button--danger"
                      disabled={deletingCaseId === caseItem.id}
                      onClick={(event) => {
                        event.stopPropagation();
                        void handleDelete(caseItem);
                      }}
                    >
                      {deletingCaseId === caseItem.id ? "Deleting..." : "Delete"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
