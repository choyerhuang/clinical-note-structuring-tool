import { apiClient } from "./client";
import type { NoteType, ParseNoteResponse } from "../types/case";

export async function parseNoteUpload(file: File, noteType?: NoteType) {
  const formData = new FormData();
  formData.append("file", file);
  if (noteType) {
    formData.append("note_type", noteType);
  }

  const response = await apiClient.post<ParseNoteResponse>("/uploads/parse-note", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}
