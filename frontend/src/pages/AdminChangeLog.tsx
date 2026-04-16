import { useState, useEffect } from 'react';
import { Lock, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router';
import { getChangeLog } from '../api/adminApi';
import { logout } from '../api/authApi';
import type { ChangeLogEntry } from '../types';

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString('en-AU', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatActionLabel(actionType: string): string {
  return actionType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getActionColor(actionType: string): { bg: string; text: string } {
  if (actionType.includes('created') || actionType.includes('reactivated'))
    return { bg: '#E8F5E9', text: '#2E7D32' };
  if (actionType.includes('modified'))
    return { bg: '#E3F2FD', text: '#185FA5' };
  if (actionType.includes('deleted'))
    return { bg: '#FFEBEE', text: '#C62828' };
  if (actionType.includes('deactivated'))
    return { bg: '#F5F5F5', text: '#757575' };
  return { bg: '#F5F5F5', text: '#757575' };
}

export function AdminChangeLog() {
  const navigate = useNavigate();

  // ── Data state ──
  const [logs, setLogs] = useState<ChangeLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // ── Date filter state ──
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  // ── Fetch logs ──
  const loadLogs = (from?: string, to?: string) => {
    setIsLoading(true);
    setError('');
    getChangeLog({ from_date: from, to_date: to })
      .then((res) => setLogs(res.items))
      .catch((err: Error) => setError(err.message || 'Could not load change log.'))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilter = () => {
    loadLogs(fromDate || undefined, toDate || undefined);
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F4F6F8' }}>
      {/* Navigation Bar */}
      <nav className="bg-white" style={{ height: '52px', borderBottom: '0.5px solid #E0DED6' }}>
        <div className="h-full px-6 flex items-center justify-between">
          {/* Left: Logo and Nav Links */}
          <div className="flex items-center gap-8">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div
                className="flex items-center justify-center"
                style={{
                  width: '28px',
                  height: '28px',
                  backgroundColor: '#185FA5',
                  borderRadius: '5px'
                }}
              >
                <span className="text-white font-semibold">T</span>
              </div>
              <span className="font-semibold" style={{ fontSize: '16px', color: '#1A1A1A' }}>
                TRIBOT
              </span>
            </div>

            {/* Nav Links */}
            <div className="flex items-center gap-6">
              <button
                onClick={() => navigate('/admin')}
                className="transition-colors"
                style={{
                  fontSize: '14px',
                  color: '#5F5E5A',
                  fontWeight: 400
                }}
              >
                Users
              </button>
              <button
                onClick={() => navigate('/admin/sessions')}
                className="transition-colors"
                style={{
                  fontSize: '14px',
                  color: '#5F5E5A',
                  fontWeight: 400
                }}
              >
                Session history
              </button>
              <button
                onClick={() => navigate('/admin/changelog')}
                className="transition-colors"
                style={{
                  fontSize: '14px',
                  color: '#185FA5',
                  fontWeight: 500
                }}
              >
                Change log
              </button>
            </div>
          </div>

          {/* Right: Admin Badge, Avatar, Divider, and Logout */}
          <div className="flex items-center gap-3">
            <div
              className="px-3 py-1"
              style={{
                border: '1px solid #A32D2D',
                borderRadius: '12px',
                fontSize: '11px',
                color: '#A32D2D',
                fontWeight: 500
              }}
            >
              Admin
            </div>
            <div
              className="flex items-center justify-center text-white font-medium"
              style={{
                width: '32px',
                height: '32px',
                backgroundColor: '#5F5E5A',
                borderRadius: '50%',
                fontSize: '13px'
              }}
            >
              AD
            </div>

            {/* Vertical Divider */}
            <div style={{ width: '1px', height: '20px', backgroundColor: '#E0DED6' }} />

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 group transition-colors"
            >
              <LogOut
                size={14}
                className="transition-colors group-hover:text-[#A32D2D]"
                style={{ color: '#5F5E5A' }}
              />
              <span
                className="transition-colors group-hover:text-[#A32D2D]"
                style={{ fontSize: '13px', color: '#5F5E5A' }}
              >
                Log out
              </span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="p-8">
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center text-[13px] text-[#5F5E5A] py-20">
            Loading change log…
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center text-[13px] text-[#A32D2D] py-20">
            {error}
          </div>
        ) : (
          <div className="bg-white" style={{ borderRadius: '12px', border: '0.5px solid #E0DED6', padding: '32px' }}>
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-2">
                <Lock size={18} style={{ color: '#5F5E5A' }} />
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: 500, color: '#1A1A1A', marginBottom: '4px' }}>
                    Change log
                  </h2>
                  <p style={{ fontSize: '13px', color: '#5F5E5A' }}>
                    Audit trail of all administrative actions
                  </p>
                </div>
              </div>

              {/* Date Range Filter */}
              <div className="flex items-center gap-2">
                <div>
                  <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>From</label>
                  <input
                    type="date"
                    value={fromDate}
                    onChange={(e) => setFromDate(e.target.value)}
                    className="outline-none"
                    style={{
                      height: '36px',
                      padding: '0 10px',
                      border: '1px solid #E0DED6',
                      borderRadius: '8px',
                      fontSize: '13px'
                    }}
                  />
                </div>
                <div>
                  <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>To</label>
                  <input
                    type="date"
                    value={toDate}
                    onChange={(e) => setToDate(e.target.value)}
                    className="outline-none"
                    style={{
                      height: '36px',
                      padding: '0 10px',
                      border: '1px solid #E0DED6',
                      borderRadius: '8px',
                      fontSize: '13px'
                    }}
                  />
                </div>
                <div className="pt-6">
                  <button
                    onClick={handleFilter}
                    className="transition-colors hover:bg-gray-50"
                    style={{
                      height: '36px',
                      padding: '0 16px',
                      border: '1px solid #E0DED6',
                      borderRadius: '8px',
                      fontSize: '14px',
                      color: '#5F5E5A'
                    }}
                  >
                    Filter
                  </button>
                </div>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: '1px solid #E0DED6' }}>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Timestamp</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Admin user</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Action type</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Target</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, idx) => {
                    const colors = getActionColor(log.action_type);
                    return (
                      <tr key={log.id} style={{ borderBottom: idx < logs.length - 1 ? '1px solid #E0DED6' : 'none' }}>
                        <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{formatTimestamp(log.timestamp)}</td>
                        <td className="py-3" style={{ fontSize: '13px', color: '#5F5E5A' }}>{log.admin_user}</td>
                        <td className="py-3">
                          <span
                            className="px-2 py-1"
                            style={{
                              fontSize: '11px',
                              borderRadius: '12px',
                              backgroundColor: colors.bg,
                              color: colors.text,
                              fontWeight: 500
                            }}
                          >
                            {formatActionLabel(log.action_type)}
                          </span>
                        </td>
                        <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{log.target}</td>
                        <td className="py-3" style={{ fontSize: '13px', color: '#5F5E5A' }}>{log.details}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
