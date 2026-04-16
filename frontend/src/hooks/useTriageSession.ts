import { useState, useCallback } from 'react';
import {
  ATSCategory,
  PatchSessionPayload,
  TriageSession,
  createSession,
  getSession,
  patchSession,
  submitSession,
} from '../api/triageApi';
import { ApiError } from '../api/apiClient';

interface UseTriageSessionReturn {
  session: TriageSession | null;
  isSubmitting: boolean;
  error: string;
  startSession: (payload?: { patient_id?: string | null; patient_language?: string; provider_id?: string }) => Promise<TriageSession | null>;
  /** PATCHes any session fields — vitals, ATS category, nurse confirmation. */
  updateSession: (patch: PatchSessionPayload) => Promise<void>;
  /** Final submit — resolves once backend confirms. */
  finaliseSession: (category: ATSCategory) => Promise<boolean>;
  clearSession: () => void;
}

export function useTriageSession(): UseTriageSessionReturn {
  const [session, setSession] = useState<TriageSession | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const startSession = useCallback(async (payload?: { patient_id?: string | null; patient_language?: string; provider_id?: string }) => {
    setError('');
    try {
      const created = await createSession(payload ?? {});
      setSession(created);
      return created;
    } catch (err: unknown) {
      // 409 = active session already exists — auto-resume it
      if (err instanceof ApiError && err.status === 409 && err.detail?.session_id) {
        try {
          const detail = await getSession(err.detail.session_id);
          setSession(detail.session);
          return detail.session;
        } catch (resumeErr: unknown) {
          console.error('[startSession] failed to resume existing session:', resumeErr);
        }
      }
      setError(err instanceof Error ? err.message : 'Could not start session.');
      return null;
    }
  }, []);

  const updateSession = useCallback(async (patch: PatchSessionPayload) => {
    if (!session) return;
    try {
      const updated = await patchSession(session.id, patch);
      setSession(updated);
    } catch (err: unknown) {
      console.error('[updateSession] error:', err);
    }
  }, [session]);

  const finaliseSession = useCallback(async (category: ATSCategory): Promise<boolean> => {
    if (!session) return false;
    setIsSubmitting(true);
    setError('');
    try {
      const response = await submitSession(session.id, category);
      setSession(response.session);
      return true;
    } catch (err: unknown) {
      console.error('[finaliseSession] error:', err);
      setError(err instanceof Error ? err.message : 'Could not submit session.');
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, [session]);

  const clearSession = useCallback(() => {
    setSession(null);
    setError('');
  }, []);

  return { session, isSubmitting, error, startSession, updateSession, finaliseSession, clearSession };
}
