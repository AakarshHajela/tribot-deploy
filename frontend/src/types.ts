export type AppMode = 'login' | 'idle' | 'active' | 'submitted' | 'history';

export interface Patient {
  id: string;
  name: string;
  mrn: string;
  language: string;
}

export interface Message {
  id: string;
  type: 'nurse' | 'patient';
  originalText: string;
  translatedText: string;
  confidence: number;
}

export interface Session {
  id: string;
  patient: Patient;
  messages: Message[];
  vitals: {
    bp: { systolic: string; diastolic: string };
    hr: string;
    temp: string;
    rr: string;
    spo2: string;
  };
  atsCategory: 1 | 2 | 3 | 4 | 5;
  startTime: Date;
  endTime: Date;
  clinician: string;
  languages: string;
}

// ---------------------------------------------------------------------------
// Admin domain types
// ---------------------------------------------------------------------------

/** Matches UserListItem from GET /api/v1/admin/users */
export interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'clinician';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

/** Matches CreateUserRequest for POST /api/v1/admin/users */
export interface CreateUserPayload {
  full_name: string;
  email: string;
  role: 'admin' | 'clinician';
}

/** Matches UpdateUserRequest for PUT /api/v1/admin/users/:id */
export interface UpdateUserPayload {
  full_name?: string;
  role?: 'admin' | 'clinician';
}

/** Matches AdminSessionItem from GET /api/v1/admin/sessions */
export interface AdminSession {
  session_id: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  patient_name: string;
  mrn: string;
  patient_language: string;
  ats_category: number | null;
  avg_translation_confidence: number | null;
}

/** Matches ChangeLogEntry from GET /api/v1/admin/change-log */
export interface ChangeLogEntry {
  id: number;
  timestamp: string;
  admin_user: string;
  action_type: string;
  target: string;
  details: string;
}
