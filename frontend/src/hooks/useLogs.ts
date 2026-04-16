import { useState, useEffect } from 'react';
import { fetchLogs, LogEntry } from '../api/logsApi';

interface UseLogsReturn {
  logs: LogEntry[];
  isLoading: boolean;
  error: string;
}

export function useLogs(): UseLogsReturn {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLogs()
      .then(setLogs)
      .catch((err: Error) => setError(err.message || 'Could not load history.'))
      .finally(() => setIsLoading(false));
  }, []);

  return { logs, isLoading, error };
}