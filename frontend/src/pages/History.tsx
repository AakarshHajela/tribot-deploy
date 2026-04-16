import { Download, ChevronDown, ChevronUp } from 'lucide-react';
import { ConfidenceBadge } from '../components/ConfidenceBadge';
import { toast } from 'sonner';
import { useHistory } from '../hooks/useHistory';
import { HistoryItem, SessionDetail, SessionDetailMessage } from '../api/triageApi';

// Helpers

function formatDuration(seconds: number): string {
  return `${Math.round(seconds / 60)} min`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

function getATSDescription(category: number | null): string {
  switch (category) {
    case 1: return 'Resuscitation — Immediate life threat';
    case 2: return 'Emergency — Within 10 min';
    case 3: return 'Urgent — Within 30 min';
    case 4: return 'Semi-urgent — Within 60 min';
    case 5: return 'Non-urgent — Within 120 min';
    default: return 'Not assigned';
  }
}

// TranscriptPanel

function TranscriptPanel({ messages }: { messages: SessionDetailMessage[] }) {
  return (
    <div className="flex-[55] bg-white rounded-lg border border-[#E0DED6] p-4 overflow-y-auto max-h-[420px]">
      <h3 className="text-[14px] font-semibold text-[#1A1A1A] mb-3">Session transcript</h3>
      <div className="space-y-3">
        {messages.map((msg) => {
          const isClinician = msg.sender === 'clinician';
          return (
            <div key={msg.id} className={`flex ${isClinician ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] flex flex-col ${isClinician ? 'items-end' : 'items-start'}`}>
                <div className="flex justify-between items-center w-full mb-0.5 px-1 gap-2">
                  <span className="text-[10px] text-[#5F5E5A]">
                    {isClinician ? 'Clinician' : 'Patient'} · {msg.source_language.toUpperCase()}
                  </span>
                  <span className="text-[10px] text-[#5F5E5A]">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                  </span>
                </div>
                <div className={`px-4 py-2.5 rounded-lg ${
                  isClinician ? 'bg-[#185FA5] text-white' : 'bg-white text-[#1A1A1A] border border-[#E0DED6]'
                }`}>
                  <p className="text-[14px] leading-relaxed">{msg.original_text}</p>
                </div>
                <div className="mt-1.5 px-1 flex items-center gap-2">
                  <p className="text-[12px] italic text-[#5F5E5A]">{msg.translated_text}</p>
                  <ConfidenceBadge confidence={msg.confidence} />
                </div>
              </div>
            </div>
          );
        })}
        {messages.length === 0 && (
          <p className="text-[13px] text-[#5F5E5A]">No messages recorded.</p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SummaryPanel
// ---------------------------------------------------------------------------

function SummaryPanel({ detail }: { detail: SessionDetail }) {
  const { session, patient } = detail;
  const v = session.vitals;

  const vitals: [string, string][] = [
    ['Blood Pressure', v.bp_systolic != null && v.bp_diastolic != null ? `${v.bp_systolic}/${v.bp_diastolic} mmHg` : '—'],
    ['Heart Rate',     v.heart_rate    != null ? `${v.heart_rate} bpm`    : '—'],
    ['Temperature',    v.temperature   != null ? `${v.temperature} °F`    : '—'],
    ['Resp. Rate',     v.respiratory_rate != null ? `${v.respiratory_rate} br/min` : '—'],
    ['SpO2',           v.spo2          != null ? `${v.spo2}%`             : '—'],
  ];

  return (
    <div className="flex-[45] bg-white rounded-lg border border-[#E0DED6] p-4 overflow-y-auto max-h-[420px]">
      <h3 className="text-[14px] font-semibold text-[#1A1A1A] mb-3">Session summary</h3>

      <div className="mb-4">
        <p className="text-[15px] font-medium text-[#1A1A1A]">{patient.full_name}</p>
        <p className="text-[12px] text-[#5F5E5A]">MRN: {patient.mrn}</p>
      </div>

      <div className="mb-4">
        <h4 className="text-[11px] uppercase text-[#5F5E5A] mb-1">Timing</h4>
        <p className="text-[13px] text-[#1A1A1A]">{formatDate(session.started_at)}</p>
        <p className="text-[12px] text-[#5F5E5A]">Duration: {formatDuration(session.duration_seconds)}</p>
      </div>

      <div className="mb-4">
        <h4 className="text-[11px] uppercase text-[#5F5E5A] mb-2">Vital signs</h4>
        <div className="space-y-1 text-[12px]">
          {vitals.map(([label, value]) => (
            <div key={label} className="flex justify-between">
              <span className="text-[#5F5E5A]">{label}</span>
              <span className="text-[#1A1A1A]">{value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <h4 className="text-[11px] uppercase text-[#5F5E5A] mb-2">ATS category</h4>
        <div className="px-3 py-2 bg-[#D94F04]/10 rounded-lg">
          <p className="text-[14px] font-semibold text-[#1A1A1A]">
            {session.ats_category ? `Category ${session.ats_category}` : 'Not assigned'}
          </p>
          <p className="text-[11px] text-[#5F5E5A] mt-0.5">{getATSDescription(session.ats_category)}</p>
        </div>
      </div>

      <div>
        <h4 className="text-[11px] uppercase text-[#5F5E5A] mb-1">Avg. translation confidence</h4>
        <p className="text-[13px] text-[#1A1A1A]">{Math.round(session.avg_translation_confidence)}%</p>
      </div>
    </div>
  );
}

// AccordionRow

function AccordionRow({
  item, isExpanded, isLoadingDetail, detail, onToggle, onDownload,
}: {
  item: HistoryItem;
  isExpanded: boolean;
  isLoadingDetail: boolean;
  detail: SessionDetail | null;
  onToggle: () => void;
  onDownload: (e: React.MouseEvent) => void;
}) {
  return (
    <>
      <tr
        onClick={onToggle}
        className="border-b border-[#E0DED6] hover:bg-[#F4F6F8] cursor-pointer transition-colors"
      >
        <td className="px-2 md:px-4 py-3 text-[12px] md:text-[13px] text-[#1A1A1A]">
          <div className="flex items-center gap-2">
            {isExpanded
              ? <ChevronUp className="w-4 h-4 text-[#5F5E5A]" />
              : <ChevronDown className="w-4 h-4 text-[#5F5E5A]" />}
            {formatDate(item.started_at)}
          </div>
        </td>
        <td className="px-2 md:px-4 py-3 text-[12px] md:text-[13px] text-[#1A1A1A]">{item.patient_name}</td>
        <td className="hidden md:table-cell px-4 py-3 text-[13px] text-[#5F5E5A]">{item.mrn}</td>
        <td className="hidden lg:table-cell px-4 py-3 text-[13px] text-[#5F5E5A]">{item.patient_language}</td>
        <td className="px-2 md:px-4 py-3">
          {item.ats_category ? (
            <span className="px-2 py-1 bg-[#D94F04]/10 text-[#D94F04] rounded-full text-[11px] font-medium">
              Cat {item.ats_category}
            </span>
          ) : (
            <span className="text-[11px] text-[#9E9C97]">—</span>
          )}
        </td>
        <td className="hidden sm:table-cell px-2 md:px-4 py-3 text-[12px] md:text-[13px] text-[#5F5E5A]">
          {formatDuration(item.duration_seconds)}
        </td>
        <td className="px-2 md:px-4 py-3">
          <button
            onClick={onDownload}
            className="flex items-center gap-1.5 px-2.5 py-1.5 border border-[#5F5E5A] text-[#5F5E5A] rounded-md text-[11px] font-medium hover:bg-[#F4F6F8] transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            PDF
          </button>
        </td>
      </tr>

      {isExpanded && (
        <tr>
          <td colSpan={7} className="bg-[#F4F6F8] p-0">
            <div className="p-4">
              {isLoadingDetail && (
                <div className="py-6 text-center text-[13px] text-[#5F5E5A]">Loading session…</div>
              )}
              {!isLoadingDetail && !detail && (
                <div className="py-6 text-center text-[13px] text-[#A32D2D]">Could not load session detail.</div>
              )}
              {detail && (
                <div className="flex gap-4">
                  <TranscriptPanel messages={detail.messages} />
                  <SummaryPanel detail={detail} />
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// Page

const TABLE_HEADERS = [
  { label: 'Date/time',     hide: '' },
  { label: 'Patient name',  hide: '' },
  { label: 'MRN',           hide: 'hidden md:table-cell' },
  { label: 'Language',      hide: 'hidden lg:table-cell' },
  { label: 'ATS category',  hide: '' },
  { label: 'Duration',      hide: 'hidden sm:table-cell' },
  { label: 'Export',        hide: '' },
];

export default function History() {
  const {
    items, isLoading, error,
    searchQuery, setSearchQuery,
    expandedId, expandedDetail, isLoadingDetail, toggleExpanded,
  } = useHistory();

  const handleDownloadPDF = (sessionId: string, patientName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    toast.info(`Downloading session report for ${patientName}…`);
  };

  return (
    <div className="pt-[52px] h-screen bg-[#F4F6F8]">
      <div className="max-w-[1440px] mx-auto h-[calc(100vh-52px)] p-4 md:p-6">
        <div className="bg-white rounded-xl p-4 md:p-6 h-full flex flex-col">

          <div className="flex items-start justify-between mb-4 md:mb-6 flex-wrap gap-3">
            <div>
              <h1 className="text-[20px] md:text-[24px] font-semibold text-[#1A1A1A] mb-1">Session history</h1>
              <p className="text-[13px] text-[#5F5E5A]">View completed triage sessions and transcripts</p>
            </div>
            <input
              type="text"
              placeholder="Search patient name, MRN…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-[36px] px-3 rounded-lg border border-[#E0DED6] text-[13px] focus:outline-none focus:ring-2 focus:ring-[#185FA5] w-[220px]"
            />
          </div>

          <div className="flex-1 overflow-auto">
            {isLoading && (
              <div className="py-12 text-center text-[13px] text-[#5F5E5A]">Loading history…</div>
            )}
            {error && (
              <div className="py-12 text-center text-[13px] text-[#A32D2D]">{error}</div>
            )}
            {!isLoading && !error && (
              <table className="w-full">
                <thead className="border-b border-[#E0DED6] bg-[#F4F6F8]">
                  <tr>
                    {TABLE_HEADERS.map(({ label, hide }) => (
                      <th key={label} className={`text-left px-2 md:px-4 py-3 text-[11px] uppercase text-[#5F5E5A] font-medium ${hide}`}>
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <AccordionRow
                      key={item.session_id}
                      item={item}
                      isExpanded={expandedId === item.session_id}
                      isLoadingDetail={isLoadingDetail && expandedId === item.session_id}
                      detail={expandedId === item.session_id ? expandedDetail : null}
                      onToggle={() => toggleExpanded(item.session_id)}
                      onDownload={(e) => handleDownloadPDF(item.session_id, item.patient_name, e)}
                    />
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-[13px] text-[#5F5E5A]">
                        No sessions found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}