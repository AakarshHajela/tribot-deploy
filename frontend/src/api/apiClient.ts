const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    public readonly detail?: any,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getAuthToken(): string | null {
  return sessionStorage.getItem('token');
}

export function clearAuthToken(): void {
  sessionStorage.removeItem('token');
}

export function setAuthToken(token: string): void {
  sessionStorage.setItem('token', token);
}

interface RequestOptions {
  unauthenticated?: boolean;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };

  if (!options.unauthenticated) {
    const token = getAuthToken();
    if (!token) {
      redirectToLogin();
      throw new ApiError('Not authenticated.');
    }
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    clearAuthToken();
    redirectToLogin();
    throw new ApiError('Session expired.', 401);
  }

  if (!response.ok) {
    let serverMessage: string | undefined;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let detail: any;
    try {
      const body = await response.json();
      detail = body?.detail;
      serverMessage = typeof detail === 'string' ? detail : detail?.message ?? body?.message;
    } catch { /* ignore */ }
    throw new ApiError(
      serverMessage ?? `Request failed with status ${response.status}`,
      response.status,
      detail,
    );
  }

  return response.json() as Promise<T>;
}

/** Hard navigation so router state is fully reset on logout/expiry. */
function redirectToLogin(): void {
  if (window.location.pathname !== '/login') {
    window.location.replace('/login');
  }
}

export const apiClient = {
  post<T>(path: string, body: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, { method: 'POST', body: JSON.stringify(body) }, options);
  },
  patch<T>(path: string, body: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }, options);
  },
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { method: 'GET' }, options);
  },
};