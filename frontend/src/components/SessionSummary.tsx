import { Session } from '../types';

interface SessionSummaryProps {
  session: Session;
  onBack: () => void;
}

export function SessionSummary({ session, onBack }: SessionSummaryProps) {
  const categoryLabels = {
    1: 'Resuscitation — Immediate · life threat',
    2: 'Emergency — seen within 10 min',
    3: 'Urgent — seen within 30 min',
    4: 'Semi-urgent — seen within 60 min',
    5: 'Non-urgent — seen within 120 min'
  };

  const categoryColors = {
    1: 'bg-[#A32D2D] text-white',
    2: 'bg-[#D94F04] text-white',
    3: 'bg-[#BA7517] text-white',
    4: 'bg-[#5F5E5A] text-white',
    5: 'bg-[#5F5E5A] text-white'
  };

  const duration = Math.round((session.endTime.getTime() - session.startTime.getTime()) / 60000);

  return (
    <div className="flex flex-col h-full bg-white rounded-xl overflow-hidden">
      {/* Header */}
      <div className="h-[32px] bg-[#F4F6F8] px-4 flex items-center justify-between border-b border-[#E0DED6] flex-shrink-0">
        <span className="text-[12px] font-medium text-[#1A1A1A]">Session summary</span>
        <span className="text-[11px] text-[#5F5E5A]">read-only</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* ATS Category */}
        <div className="mb-4">
          <div className={`px-4 py-2.5 rounded-full text-center text-[14px] font-medium ${categoryColors[session.atsCategory]}`}>
            Category {session.atsCategory} — {categoryLabels[session.atsCategory]}
          </div>
        </div>

        {/* Summary text */}
        <div className="mb-4">
          <h3 className="text-[11px] uppercase text-[#5F5E5A] mb-2">Session summary</h3>
          <p className="text-[13px] text-[#1A1A1A] leading-relaxed">
            Patient presented with chest pain and shortness of breath beginning approximately one hour prior to arrival. Nurse conducted bilingual triage assessment in English and Arabic. Patient confirmed severity of chest pain as high. No prior cardiac history mentioned. Vitals recorded within normal range except elevated heart rate. ATS Category {session.atsCategory} assigned based on symptom profile.
          </p>
        </div>

        {/* Metadata */}
        <div className="border-t border-[#E0DED6] pt-3">
          <h3 className="text-[11px] uppercase text-[#5F5E5A] mb-2">Session metadata</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-[13px]">
              <span className="text-[#5F5E5A]">Start time</span>
              <span className="text-[#1A1A1A]">
                {session.startTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
              </span>
            </div>
            <div className="flex justify-between text-[13px]">
              <span className="text-[#5F5E5A]">End time</span>
              <span className="text-[#1A1A1A]">
                {session.endTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
              </span>
            </div>
            <div className="flex justify-between text-[13px]">
              <span className="text-[#5F5E5A]">Duration</span>
              <span className="text-[#1A1A1A]">{duration} min</span>
            </div>
            <div className="flex justify-between text-[13px]">
              <span className="text-[#5F5E5A]">Clinician</span>
              <span className="text-[#1A1A1A]">{session.clinician}</span>
            </div>
            <div className="flex justify-between text-[13px]">
              <span className="text-[#5F5E5A]">Languages used</span>
              <span className="text-[#1A1A1A]">{session.languages}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Back button */}
      <div className="p-4 border-t border-[#E0DED6] flex-shrink-0">
        <button 
          onClick={onBack}
          className="w-full px-4 py-2 border border-[#5F5E5A] text-[#5F5E5A] rounded-md text-[13px] font-medium hover:bg-[#F4F6F8] transition-colors"
        >
          Back to workspace
        </button>
      </div>
    </div>
  );
}