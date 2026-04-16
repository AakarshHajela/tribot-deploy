import { createContext, useContext, useState, ReactNode } from 'react';
import { AppMode, Patient, Session } from '../types';

interface AppContextType {
  mode: AppMode;
  setMode: (mode: AppMode) => void;
  currentPatient: Patient | null;
  setCurrentPatient: (patient: Patient | null) => void;
  sessions: Session[];
  addSession: (session: Session) => void;
  currentSession: Session | null;
  setCurrentSession: (session: Session | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Demo data
const demoSessions: Session[] = [
  {
    id: '1',
    patient: {
      id: '1',
      name: 'Ahmed Al-Mansoori',
      mrn: 'MRN-2024-001234',
      language: 'Arabic'
    },
    messages: [
      {
        id: '1',
        type: 'nurse',
        originalText: 'Hello, can you describe your symptoms?',
        translatedText: 'مرحبا، هل يمكنك وصف الأعراض الخاصة بك؟',
        confidence: 96
      },
      {
        id: '2',
        type: 'patient',
        originalText: 'ألم في الصدر وضيق في التنفس',
        translatedText: 'Chest pain and shortness of breath',
        confidence: 94
      }
    ],
    vitals: {
      bp: { systolic: '128', diastolic: '82' },
      hr: '88',
      temp: '98.6',
      rr: '18',
      spo2: '96'
    },
    atsCategory: 2,
    startTime: new Date('2024-03-24T09:15:00'),
    endTime: new Date('2024-03-24T09:28:00'),
    clinician: 'Sarah Chen',
    languages: 'EN ↔ AR'
  }
];

export function AppProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<AppMode>('idle');
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null);
  const [sessions, setSessions] = useState<Session[]>(demoSessions);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);

  const addSession = (session: Session) => {
    setSessions([...sessions, session]);
  };

  return (
    <AppContext.Provider
      value={{
        mode,
        setMode,
        currentPatient,
        setCurrentPatient,
        sessions,
        addSession,
        currentSession,
        setCurrentSession,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
