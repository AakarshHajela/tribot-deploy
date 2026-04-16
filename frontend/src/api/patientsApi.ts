import { apiClient } from './apiClient';

export interface Patient {
  id: string;
  mrn: string;
  full_name: string;
  patient_language: string;
  created_at: string;
}

interface PatientsResponse {
  total: number;
  items: Patient[];
}

export function listPatients(): Promise<Patient[]> {
  return apiClient.get<PatientsResponse>('/api/v1/patients').then((r) => r.items);
}