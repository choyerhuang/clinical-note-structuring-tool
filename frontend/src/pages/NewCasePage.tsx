import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

import { createCase } from "../api/cases";
import { parseNoteUpload } from "../api/uploads";
import { NoteSourceSection } from "../components/case/NoteSourceSection";
import type { NoteType } from "../types/case";

function buildMergedClinicalNote({
  erNote,
  hpNote,
  originalNote,
}: {
  erNote: string;
  hpNote: string;
  originalNote: string;
}) {
  const normalizedOriginal = originalNote.trim();
  const normalizedEr = erNote.trim();
  const normalizedHp = hpNote.trim();

  if (normalizedOriginal && !normalizedEr && !normalizedHp) {
    return normalizedOriginal;
  }

  const sections = [
    normalizedEr ? `[ER NOTE]\n${normalizedEr}` : null,
    normalizedHp ? `[H&P NOTE]\n${normalizedHp}` : null,
    normalizedOriginal ? `[ORIGINAL CLINICAL NOTE]\n${normalizedOriginal}` : null,
  ].filter(Boolean);

  return sections.join("\n\n");
}

export function NewCasePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [originalNote, setOriginalNote] = useState("");
  const [erNote, setErNote] = useState("");
  const [hpNote, setHpNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadState, setUploadState] = useState<
    Record<NoteType, { isUploading: boolean; error: string | null; warning: string | null }>
  >({
    er: { isUploading: false, error: null, warning: null },
    hp: { isUploading: false, error: null, warning: null },
  });

  const handleUpload = async (file: File, noteType: NoteType) => {
    setUploadState((current) => ({
      ...current,
      [noteType]: { isUploading: true, error: null, warning: null },
    }));

    try {
      const result = await parseNoteUpload(file, noteType);
      if (result.text) {
        if (noteType === "er") {
          setErNote(result.text);
        } else {
          setHpNote(result.text);
        }
      }

      setUploadState((current) => ({
        ...current,
        [noteType]: {
          isUploading: false,
          error: result.error,
          warning: result.warning,
        },
      }));
    } catch (err) {
      const uploadError = axios.isAxiosError(err)
        ? err.response?.data?.error ?? "Unable to parse file."
        : "An unexpected upload error occurred.";

      setUploadState((current) => ({
        ...current,
        [noteType]: {
          isUploading: false,
          error: uploadError,
          warning: null,
        },
      }));
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const mergedNote = buildMergedClinicalNote({
      erNote,
      hpNote,
      originalNote,
    });

    if (!mergedNote.trim()) {
      setError("Please provide note content in Original Clinical Note, ER Note, or H&P Note.");
      setIsSubmitting(false);
      return;
    }

    try {
      const createdCase = await createCase({
        title,
        original_note: mergedNote,
      });
      navigate(`/cases/${createdCase.id}`);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError("Unable to create the case. Please review the inputs and try again.");
      } else {
        setError("An unexpected error occurred while creating the case.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-centered">
      <div className="page-intro">
        <h1 className="page-title">Create New Case</h1>
        <p className="page-description">
          Capture the raw clinical note first, then generate structured output for review.
        </p>
      </div>

      <form className="card form-card" onSubmit={handleSubmit}>
        <div className="card__header">
          <h2 className="card__title">New Case</h2>
        </div>

        <div className="stack">
          <div className="form-field">
            <label htmlFor="title" className="field-label">
              Title
            </label>
            <input
              id="title"
              className="input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Chest pain evaluation"
              required
            />
          </div>

          <NoteSourceSection
            id="er_note"
            title="ER Note"
            value={erNote}
            onChange={setErNote}
            noteType="er"
            onUpload={handleUpload}
            uploadState={uploadState.er}
            placeholder="Paste or upload the ER note here..."
          />

          <NoteSourceSection
            id="hp_note"
            title="H&P Note"
            value={hpNote}
            onChange={setHpNote}
            noteType="hp"
            onUpload={handleUpload}
            uploadState={uploadState.hp}
            placeholder="Paste or upload the H&P note here..."
          />

          <NoteSourceSection
            id="original_note"
            title="Original Clinical Note"
            value={originalNote}
            onChange={setOriginalNote}
            placeholder="Paste or type the original clinical note here..."
          />

          {error ? <div className="error-banner">{error}</div> : null}

          <div className="button-row">
            <button className="button button--primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Case"}
            </button>
            <Link to="/cases" className="button button--secondary button--link">
              View Saved Cases
            </Link>
          </div>
        </div>
      </form>
    </div>
  );
}
