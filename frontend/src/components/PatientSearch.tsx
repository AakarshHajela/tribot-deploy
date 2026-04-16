import { useState, useRef, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Patient } from '../types';

interface PatientSearchProps {
  onSelectPatient: (patient: Patient) => void;
  disabled?: boolean;
}

const demoPatients: Patient[] = [
  { id: '1', name: 'Ahmed Al-Mansoori', mrn: 'MRN-2024-001234', language: 'Arabic' },
  { id: '2', name: 'Maria Garcia', mrn: 'MRN-2024-001235', language: 'Spanish' },
  { id: '3', name: 'Fatima Hassan', mrn: 'MRN-2024-001237', language: 'Arabic' }
];

export function PatientSearch({ onSelectPatient, disabled = false }: PatientSearchProps) {
  const [searchText, setSearchText] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredPatients = searchText.trim()
    ? demoPatients.filter(
        (p) =>
          p.name.toLowerCase().includes(searchText.toLowerCase()) ||
          p.mrn.toLowerCase().includes(searchText.toLowerCase())
      )
    : [];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (patient: Patient) => {
    onSelectPatient(patient);
    setSearchText('');
    setShowDropdown(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5F5E5A]" />
        <input
          ref={inputRef}
          type="text"
          value={searchText}
          onChange={(e) => {
            setSearchText(e.target.value);
            setShowDropdown(true);
          }}
          onFocus={() => searchText && setShowDropdown(true)}
          disabled={disabled}
          placeholder="Search patient by ID or name..."
          className={`w-full md:w-[280px] lg:w-[320px] h-[32px] pl-9 pr-3 rounded-md border border-[#E0DED6] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#185FA5] focus:ring-offset-0 ${
            disabled ? 'opacity-40 cursor-not-allowed' : ''
          }`}
        />
      </div>

      {showDropdown && filteredPatients.length > 0 && (
        <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-[#E0DED6] z-50 max-h-[240px] overflow-y-auto">
          {filteredPatients.map((patient) => (
            <button
              key={patient.id}
              onClick={() => handleSelect(patient)}
              className="w-full px-4 py-3 text-left hover:bg-[#F4F6F8] transition-colors border-b border-[#E0DED6] last:border-b-0"
            >
              <div className="text-[13px] font-medium text-[#1A1A1A]">{patient.name}</div>
              <div className="text-[11px] text-[#5F5E5A] mt-0.5">
                {patient.mrn} · {patient.language}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}