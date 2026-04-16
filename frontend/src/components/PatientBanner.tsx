import { Patient } from '../types';

interface PatientBannerProps {
  patient: Patient | null;
  isLive?: boolean;
}

export function PatientBanner({ patient, isLive = false }: PatientBannerProps) {
  if (!patient) return null;

  return (
    <div className="md:hidden bg-[#F4F6F8] px-4 py-2 border-b border-[#E0DED6] flex items-center justify-between">
      <div className="flex items-center gap-2">
        {isLive && <span className="w-2 h-2 bg-[#A32D2D] rounded-full animate-pulse"></span>}
        <span className="text-[13px] font-medium text-[#1A1A1A]">
          {patient.name} · {patient.language.substring(0, 2).toUpperCase()}
        </span>
      </div>
      {isLive && <span className="text-[11px] text-[#A32D2D] font-medium">LIVE</span>}
    </div>
  );
}
