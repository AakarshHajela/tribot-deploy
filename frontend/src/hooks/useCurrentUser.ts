import { useState, useEffect } from 'react';
import { fetchCurrentUser, CurrentUser } from '../api/authApi';

interface UseCurrentUserReturn {
  user: CurrentUser | null;
  isLoading: boolean;
  /** True once the auth check has completed (success or failure). */
  isResolved: boolean;
}

/**
 * Fetches the current user once on mount.
 * On 401 the apiClient handles the redirect, so this hook only needs to
 * surface the user object and loading state for the rest of the UI.
 */
export function useCurrentUser(): UseCurrentUserReturn {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false));
  }, []);

  return { user, isLoading, isResolved: !isLoading };
}