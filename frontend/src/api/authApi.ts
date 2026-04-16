import { apiClient, setAuthToken, clearAuthToken } from './apiClient';

export interface CurrentUser {
  email: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  return apiClient.get<CurrentUser>('/api/v1/auth/me');
}

/**
 * Authenticates the user and stores the token.
 * Returns the resolved CurrentUser so callers can set state immediately.
 */
export async function login(credentials: LoginCredentials): Promise<CurrentUser> {
  const data = await apiClient.post<LoginResponse>(
    '/api/v1/auth/login',
    credentials,
    { unauthenticated: true },
  );
  setAuthToken(data.access_token);
  return fetchCurrentUser();
}

export function logout(): void {
  clearAuthToken();
  window.location.replace('/login');
}