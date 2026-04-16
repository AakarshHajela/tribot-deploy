/**
 * useTranslation.ts
 *
 * Encapsulates the async translation lifecycle: loading, error, and result
 * states. The component only needs to call `translate(params)` and react to
 * the returned state — all fetch logic is invisible to it.
 */

import { useState, useCallback } from 'react';
import { translateText, TranslationRequest, TranslationResponse } from '../api/translationApi';
import { ApiError } from '../api/apiClient';

interface UseTranslationState {
  isTranslating: boolean;
  error: string;
  result: TranslationResponse | null;
}

interface UseTranslationReturn extends UseTranslationState {
  translate: (params: TranslationRequest) => Promise<TranslationResponse | null>;
  clearError: () => void;
  clearResult: () => void;
}

export function useTranslation(): UseTranslationReturn {
  const [state, setState] = useState<UseTranslationState>({
    isTranslating: false,
    error: '',
    result: null,
  });

  const translate = useCallback(
    async (params: TranslationRequest): Promise<TranslationResponse | null> => {
      setState((prev) => ({ ...prev, isTranslating: true, error: '', result: null }));

      try {
        const response = await translateText(params);
        setState((prev) => ({ ...prev, result: response, isTranslating: false }));
        return response;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : 'An unexpected error occurred during translation.';
        setState((prev) => ({ ...prev, error: message, isTranslating: false }));
        return null;
      }
    },
    [],
  );

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: '' }));
  }, []);

  const clearResult = useCallback(() => {
    setState((prev) => ({ ...prev, result: null }));
  }, []);

  return {
    ...state,
    translate,
    clearError,
    clearResult,
  };
}
