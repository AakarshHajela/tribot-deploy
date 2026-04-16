import { apiClient, ApiError } from './apiClient';
import type {
  AdminUser,
  AdminSession,
  ChangeLogEntry,
  CreateUserPayload,
  UpdateUserPayload,
} from '../types';

// ── Response envelope types (internal to this module) ──

interface UsersListResponse {
  items: AdminUser[];
  total: number;
}

interface CreateUserResponse {
  user: AdminUser;
  temporary_password: string;
}

interface AdminSessionsResponse {
  items: AdminSession[];
  total: number;
}

interface ChangeLogResponse {
  items: ChangeLogEntry[];
  total: number;
}

// ── Query param shapes ──

export interface ListUsersParams {
  search?: string;
}

export interface ListSessionsParams {
  search?: string;
  limit?: number;
  offset?: number;
}

export interface GetChangeLogParams {
  from_date?: string;  // ISO date string, e.g. "2024-03-01"
  to_date?: string;    // ISO date string, e.g. "2024-03-31"
  limit?: number;
  offset?: number;
}

// ── Helpers ──

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

function buildQuery(params: object): string {
  const entries = Object.entries(params as Record<string, string | number | undefined>).filter(
    ([, v]) => v !== undefined,
  );
  if (entries.length === 0) return '';
  const qs = entries
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  return `?${qs}`;
}

/**
 * Handles PUT and DELETE verbs, which apiClient does not expose.
 * Mirrors the same auth header, 401 redirect, and error handling
 * pattern used in apiClient.ts.
 */
async function requestWithBody<T>(
  method: 'PUT' | 'DELETE',
  path: string,
  body?: unknown,
): Promise<T> {
  const token = sessionStorage.getItem('token');
  if (!token) {
    window.location.replace('/login');
    throw new ApiError('Not authenticated.');
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    sessionStorage.removeItem('token');
    window.location.replace('/login');
    throw new ApiError('Session expired.', 401);
  }

  if (!response.ok) {
    let serverMessage: string | undefined;
    try {
      const json = await response.json();
      serverMessage = json?.detail ?? json?.message;
    } catch { /* ignore */ }
    throw new ApiError(
      serverMessage ?? `Request failed with status ${response.status}`,
      response.status,
    );
  }

  // 204 No Content — return undefined cast to T
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// ── User management ──

export function listUsers(params: ListUsersParams = {}): Promise<UsersListResponse> {
  return apiClient.get<UsersListResponse>(`/api/v1/admin/users${buildQuery(params)}`);
}

export function createUser(data: CreateUserPayload): Promise<CreateUserResponse> {
  return apiClient.post<CreateUserResponse>('/api/v1/admin/users', data);
}

export function getUser(userId: string): Promise<AdminUser> {
  return apiClient.get<AdminUser>(`/api/v1/admin/users/${userId}`);
}

export function updateUser(userId: string, data: UpdateUserPayload): Promise<AdminUser> {
  return requestWithBody<AdminUser>('PUT', `/api/v1/admin/users/${userId}`, data);
}

export function deleteUser(userId: string): Promise<void> {
  return requestWithBody<void>('DELETE', `/api/v1/admin/users/${userId}`);
}

export function deactivateUser(userId: string): Promise<AdminUser> {
  return apiClient.post<AdminUser>(`/api/v1/admin/users/${userId}/deactivate`, {});
}

export function reactivateUser(userId: string): Promise<AdminUser> {
  return apiClient.post<AdminUser>(`/api/v1/admin/users/${userId}/reactivate`, {});
}

// ── Change log ──

export function getChangeLog(params: GetChangeLogParams = {}): Promise<ChangeLogResponse> {
  return apiClient.get<ChangeLogResponse>(`/api/v1/admin/change-log${buildQuery(params)}`);
}

// ── Session history ──

export function listSessions(params: ListSessionsParams = {}): Promise<AdminSessionsResponse> {
  return apiClient.get<AdminSessionsResponse>(`/api/v1/admin/sessions${buildQuery(params)}`);
}

export function deleteSession(sessionId: string): Promise<void> {
  return requestWithBody<void>('DELETE', `/api/v1/admin/sessions/${sessionId}`);
}
