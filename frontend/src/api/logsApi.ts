import { apiClient } from './apiClient';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RawLogEntry {
  id?: number;
  session_id?: string;
  timestamp?: string;
  clinician_id?: string;
  source_language?: string;
  target_language?: string;
  confidence_score?: number;
  escalation_flag?: boolean;
  source_text?: string;
  translated_output?: string;
}

interface RawLogsResponse {
  items: RawLogEntry[];
}

export interface TranscriptLine {
  speaker: 'Source' | 'Translation';
  text: string;
}

export interface LogEntry {
  id: string;
  date: string;
  patient: string;
  source: string;
  target: string;
  confidence: number;
  risk: 'High' | 'Low';
  transcript: TranscriptLine[];
}

// ---------------------------------------------------------------------------
// Mapping
// ---------------------------------------------------------------------------

function mapRawLog(log: RawLogEntry): LogEntry {
  return {
    id: log.id ? `#TR-${log.id}` : `#${log.session_id?.substring(0, 6) ?? 'N/A'}`,
    date: log.timestamp ? log.timestamp.split('T')[0] : 'Unknown',
    patient: log.clinician_id ? log.clinician_id.substring(0, 8) : 'Unknown',
    source: (log.source_language ?? 'EN').toUpperCase(),
    target: (log.target_language ?? 'AR').toUpperCase(),
    confidence: log.confidence_score ?? 0,
    risk: log.escalation_flag ? 'High' : 'Low',
    transcript: [
      { speaker: 'Source', text: log.source_text ?? '' },
      { speaker: 'Translation', text: log.translated_output ?? '' },
    ],
  };
}

// ---------------------------------------------------------------------------
// API call
// ---------------------------------------------------------------------------

export async function fetchLogs(): Promise<LogEntry[]> {
  const data = await apiClient.get<RawLogsResponse>('/api/v1/logs');
  return (data.items ?? []).map(mapRawLog);
}