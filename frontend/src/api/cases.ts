import { apiClient } from "./client";
import type {
  CaseDetail,
  CaseSummary,
  CreateCasePayload,
  SaveEditedResultPayload,
} from "../types/case";

export async function listCases() {
  const response = await apiClient.get<CaseSummary[]>("/cases/");
  return response.data;
}

export async function createCase(payload: CreateCasePayload) {
  const response = await apiClient.post<CaseDetail>("/cases/", payload);
  return response.data;
}

export async function getCase(id: number) {
  const response = await apiClient.get<CaseDetail>(`/cases/${id}/`);
  return response.data;
}

export async function generateCase(id: number) {
  const response = await apiClient.post<CaseDetail>(`/cases/${id}/generate/`);
  return response.data;
}

export async function saveCase(id: number, payload: SaveEditedResultPayload) {
  const response = await apiClient.put<CaseDetail>(`/cases/${id}/save/`, payload);
  return response.data;
}

export async function deleteCase(id: number) {
  const response = await apiClient.delete<{ success: boolean }>(`/cases/${id}/`);
  return response.data;
}
