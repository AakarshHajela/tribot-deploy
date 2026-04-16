/**
 * translationApi.ts
 *
 * All translation-related backend calls.
 */

import { apiClient } from './apiClient';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TranslationRequest {
  source_language: string;
  target_language: string;
  source_text: string;
  session_id?: string | null;
  patient_id?: string | null;
}

export interface TranslationResponse {
  translated_text: string;
  /** Confidence score 0–100 returned by the backend (if available). */
  confidence?: number;
}

// ---------------------------------------------------------------------------
// Payload builder
// ---------------------------------------------------------------------------

/**
 * Constructs the translation request payload.
 *
 * Keeping this as a pure function makes it trivial to unit-test and easy
 * to extend (e.g. add session_id) without touching the call site.
 */
export function buildTranslationPayload(
  params: TranslationRequest,
): TranslationRequest {
  return {
    source_language: params.source_language,
    target_language: params.target_language,
    source_text: params.source_text,
    session_id: params.session_id ?? null,
  };
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

/**
 * Sends a translation request to the backend and returns the result.
 */
export async function translateText(
  params: TranslationRequest,
): Promise<TranslationResponse> {
  const payload = buildTranslationPayload(params);
  return apiClient.post<TranslationResponse>('/api/v1/translate', payload);
}
