import { usePatients } from '../hooks/usePatients';
import { Patient } from '../api/patientsApi';

interface SelectPatientModalProps {
  isOpen: boolean;
  onSelectPatient: (patient: Patient) => void;
}

export function SelectPatientModal({ isOpen, onSelectPatient }: SelectPatientModalProps) {
  const { filtered, isLoading, error, searchQuery, setSearchQuery } = usePatients();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 flex flex-col overflow-hidden max-h-[80vh]">

        {/* Header */}
        <div className="px-6 pt-6 pb-4 border-b border-[#E0DED6]">
          <h2 className="text-[18px] font-semibold text-[#1A1A1A] mb-3">Select patient</h2>
          <input
            type="text"
            placeholder="Search by name, MRN, or language…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            autoFocus
            className="w-full h-[38px] px-3 rounded-lg border border-[#E0DED6] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#185FA5]"
          />
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="py-10 text-center text-[13px] text-[#5F5E5A]">Loading patients…</div>
          )}

          {error && (
            <div className="py-10 text-center text-[13px] text-[#A32D2D]">{error}</div>
          )}

          {!isLoading && !error && filtered.length === 0 && (
            <div className="py-10 text-center text-[13px] text-[#5F5E5A]">No patients found.</div>
          )}

          {!isLoading && !error && filtered.map((patient) => (
            <button
              key={patient.id}
              onClick={() => onSelectPatient(patient)}
              className="w-full px-6 py-3.5 flex items-center justify-between hover:bg-[#F4F6F8] transition-colors border-b border-[#E0DED6] last:border-0 text-left"
            >
              <div>
                <p className="text-[14px] font-medium text-[#1A1A1A]">{patient.full_name}</p>
                <p className="text-[12px] text-[#5F5E5A] mt-0.5">
                  MRN {patient.mrn}
                  <span className="mx-1.5 text-[#C8C6C0]">·</span>
                  {patient.patient_language}
                </p>
              </div>
              <span className="text-[#C8C6C0] text-[18px] leading-none ml-4">›</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}