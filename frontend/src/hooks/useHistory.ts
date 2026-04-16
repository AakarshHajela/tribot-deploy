import { useState, useEffect, useCallback } from 'react';
import { HistoryItem, SessionDetail, listHistory, getSessionDetail } from '../api/triageApi';

interface UseHistoryReturn {
  items: HistoryItem[];
  total: number;
  isLoading: boolean;
  error: string;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  
  // Accordion
  expandedId: string | null;
  expandedDetail: SessionDetail | null;
  isLoadingDetail: boolean;
  toggleExpanded: (sessionId: string) => void;
}

export function useHistory(): UseHistoryReturn {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<SessionDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  // Cache detail responses so re-opening a row doesn't re-fetch
  const [detailCache, setDetailCache] = useState<Record<string, SessionDetail>>({});

  useEffect(() => {
    setIsLoading(true);
    setError('');
    listHistory({ q: searchQuery || undefined, limit: 50 })
      .then((r) => { setItems(r.items); setTotal(r.total); })
      .catch((err: Error) => setError(err.message || 'Could not load history.'))
      .finally(() => setIsLoading(false));
  }, [searchQuery]);

  const toggleExpanded = useCallback(async (sessionId: string) => {
    // Collapse if already open
    if (expandedId === sessionId) {
      setExpandedId(null);
      setExpandedDetail(null);
      return;
    }

    setExpandedId(sessionId);

    // Serve from cache if available
    if (detailCache[sessionId]) {
      setExpandedDetail(detailCache[sessionId]);
      return;
    }

    setIsLoadingDetail(true);
    setExpandedDetail(null);
    try {
      const detail = await getSessionDetail(sessionId);
      setDetailCache((prev) => ({ ...prev, [sessionId]: detail }));
      setExpandedDetail(detail);
    } catch {
    } finally {
      setIsLoadingDetail(false);
    }
  }, [expandedId, detailCache]);

  return {
    items, total, isLoading, error,
    searchQuery, setSearchQuery,
    expandedId, expandedDetail, isLoadingDetail, toggleExpanded,
  };
}