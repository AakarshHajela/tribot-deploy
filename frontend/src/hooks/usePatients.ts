import { useState, useEffect, useMemo } from 'react';
import { listPatients, Patient } from '../api/patientsApi';

interface UsePatientsReturn {
  patients: Patient[];
  filtered: Patient[];
  isLoading: boolean;
  error: string;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

export function usePatients(): UsePatientsReturn {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    listPatients()
      .then(setPatients)
      .catch((err: Error) => setError(err.message || 'Could not load patients.'))
      .finally(() => setIsLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return patients;
    return patients.filter(
      (p) =>
        p.full_name.toLowerCase().includes(q) ||
        p.mrn.toLowerCase().includes(q) ||
        p.patient_language.toLowerCase().includes(q),
    );
  }, [patients, searchQuery]);

  return { patients, filtered, isLoading, error, searchQuery, setSearchQuery };
}