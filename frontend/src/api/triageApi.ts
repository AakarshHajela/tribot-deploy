import { apiClient } from './apiClient';
import { Message } from '../types';

// ---------------------------------------------------------------------------
// Types — raw backend shapes
// ---------------------------------------------------------------------------

export type ATSCategory = 1 | 2 | 3 | 4 | 5;

export interface TriageSession {
  id: string;
  patient_id: string | null;
  status: 'active' | 'submitted';
  ats_category: ATSCategory | null;
  created_at: string;
  submitted_at: string | null;
  messages: TriageMessage[];
}

export interface TriageMessage {
  id: string;
  session_id: string;
  source_language: string;
  target_language: string;
  source_text: string;
  translated_text: string;
  confidence: number;
  sender_type: 'nurse' | 'patient';
  created_at: string;
}

export interface TriageSessionDetailResponse {
  session: TriageSession;
  patient: {
    id: string;
    mrn: string;
    full_name: string;
    patient_language: string;
    created_at: string;
  };
  messages: TriageMessage[];
}

interface CreateSessionPayload {
  patient_id?: string | null;
  patient_language?: string;
  provider_id?: string;
}

export interface PatchSessionPayload {
  patient_language?: string;
  bp_systolic?: number;
  bp_diastolic?: number;
  heart_rate?: number;
  temperature?: number;
  respiratory_rate?: number;
  spo2?: number;
  ats_category?: ATSCategory | null;
  nurse_confirmed_ats?: boolean;
}

interface PostMessagePayload {
  sender: 'clinician' | 'patient';
  original_text: string;
  source_language: string;
  target_language: string;
  translated_text: string;
  confidence: number;
}

interface SubmitSessionResponse {
  session: TriageSession;
  patient_name: string;
  message: string;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export function createSession(payload: CreateSessionPayload): Promise<TriageSession> {
  return apiClient.post<TriageSession>('/api/v1/triage/sessions', payload);
}


export function getSession(sessionId: string): Promise<TriageSessionDetailResponse> {
  return apiClient.get<TriageSessionDetailResponse>(`/api/v1/triage/sessions/${sessionId}`);
}

export function patchSession(sessionId: string, patch: PatchSessionPayload): Promise<TriageSession> {
  return apiClient.patch<TriageSession>(`/api/v1/triage/sessions/${sessionId}`, patch);
}

export function postMessage(sessionId: string, payload: PostMessagePayload): Promise<TriageMessage> {
  return apiClient.post<TriageMessage>(`/api/v1/triage/sessions/${sessionId}/messages`, payload);
}

export function submitSession(sessionId: string, ats_category: ATSCategory): Promise<SubmitSessionResponse> {
  return apiClient.post<SubmitSessionResponse>(`/api/v1/triage/sessions/${sessionId}/submit`, { ats_category });
}

export function getSessionLogs(sessionId: string): Promise<TriageMessage[]> {
  return apiClient.get<TriageMessage[]>(`/api/v1/triage/sessions/${sessionId}/logs`);
}

/** Maps a backend TriageMessage to the frontend Message type. */
export function toFrontendMessage(msg: TriageMessage): Message {
  return {
    id: msg.id,
    type: msg.sender_type,
    originalText: msg.source_text,
    translatedText: msg.translated_text,
    confidence: msg.confidence,
  };
}

export interface HistoryItem {
  session_id: string;
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  patient_language: string;
  ats_category: ATSCategory | null;
  patient_id: string;
  mrn: string;
  patient_name: string;
  bp_systolic: number | null;
  bp_diastolic: number | null;
  heart_rate: number | null;
  temperature: number | null;
  respiratory_rate: number | null;
  spo2: number | null;
  avg_translation_confidence: number;
}
 
interface HistoryResponse {
  total: number;
  items: HistoryItem[];
}
 
export interface SessionDetailMessage {
  id: number;
  session_id: string;
  sender: string;
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  confidence: number;
  created_at: string;
}
 
export interface SessionDetailVitals {
  bp_systolic: number | null;
  bp_diastolic: number | null;
  heart_rate: number | null;
  temperature: number | null;
  respiratory_rate: number | null;
  spo2: number | null;
}
 
export interface SessionDetail {
  session: {
    id: string;
    patient_id: string;
    provider_id: string;
    status: string;
    started_at: string;
    ended_at: string;
    duration_seconds: number;
    patient_language: string;
    vitals: SessionDetailVitals;
    ats_category: ATSCategory | null;
    nurse_confirmed_ats: boolean;
    avg_translation_confidence: number;
  };
  patient: {
    id: string;
    mrn: string;
    full_name: string;
    patient_language: string;
    created_at: string;
  };
  messages: SessionDetailMessage[];
}
 
// History API calls
 
export function listHistory(params?: { q?: string; limit?: number; offset?: number }): Promise<HistoryResponse> {
  const query = new URLSearchParams();
  if (params?.q) query.set('q', params.q);
  if (params?.limit != null) query.set('limit', String(params.limit));
  if (params?.offset != null) query.set('offset', String(params.offset));
  const qs = query.toString();
  return apiClient.get<HistoryResponse>(`/api/v1/triage/history${qs ? `?${qs}` : ''}`);
}
 
export function getSessionDetail(sessionId: string): Promise<SessionDetail> {
  return apiClient.get<SessionDetail>(`/api/v1/triage/sessions/${sessionId}`);
}
 
