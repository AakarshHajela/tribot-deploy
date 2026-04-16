import { useState, useEffect, Fragment } from 'react';
import { AlertCircle, ChevronDown, Download, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router';
import { listSessions, deleteSession } from '../api/adminApi';
import { logout } from '../api/authApi';
import type { AdminSession } from '../types';

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-AU', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function AdminSessionHistory() {
  const navigate = useNavigate();

  // ── Data state ──
  const [sessions, setSessions] = useState<AdminSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // ── Expanded row ──
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  // ── Delete modal ──
  const [deleteTarget, setDeleteTarget] = useState<AdminSession | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  // ── Fetch sessions ──
  useEffect(() => {
    setIsLoading(true);
    setError('');
    listSessions()
      .then((res) => setSessions(res.items))
      .catch((err: Error) => setError(err.message || 'Could not load sessions.'))
      .finally(() => setIsLoading(false));
  }, []);

  const handleLogout = () => {
    logout();
  };

  // ── Delete session ──
  const handleDeleteSession = () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    setDeleteError('');
    deleteSession(deleteTarget.session_id)
      .then(() => {
        setSessions((prev) => prev.filter((s) => s.session_id !== deleteTarget.session_id));
        setShowDeleteModal(false);
        setDeleteTarget(null);
      })
      .catch((err: Error) => setDeleteError(err.message || 'Could not delete session.'))
      .finally(() => setIsDeleting(false));
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
                  color: '#185FA5',
                  fontWeight: 500
                }}
              >
                Session history
              </button>
              <button
                onClick={() => navigate('/admin/changelog')}
                className="transition-colors"
                style={{
                  fontSize: '14px',
                  color: '#5F5E5A',
                  fontWeight: 400
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
            Loading sessions…
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center text-[13px] text-[#A32D2D] py-20">
            {error}
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center gap-2 px-4 py-3" style={{ backgroundColor: '#FAEEDA', border: '1px solid #EF9F27', borderRadius: '8px' }}>
              <AlertCircle size={16} style={{ color: '#854F0B' }} />
              <span style={{ fontSize: '13px', color: '#854F0B' }}>
                Note: All actions in this view are recorded in the change log.
              </span>
            </div>

            <div className="bg-white" style={{ borderRadius: '12px', border: '0.5px solid #E0DED6', padding: '32px' }}>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={{ borderBottom: '1px solid #E0DED6' }}>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500, width: '30px' }}></th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Date/Time</th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Patient name</th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>MRN</th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Language</th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>ATS Category</th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Duration</th>
                      <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.map((session) => (
                      <Fragment key={session.session_id}>
                        <tr
                          className="cursor-pointer hover:bg-gray-50 transition-colors"
                          onClick={() => setExpandedRow(expandedRow === session.session_id ? null : session.session_id)}
                          style={{ borderBottom: expandedRow === session.session_id ? 'none' : '1px solid #E0DED6' }}
                        >
                          <td className="py-3">
                            <ChevronDown
                              size={16}
                              style={{
                                color: '#5F5E5A',
                                transform: expandedRow === session.session_id ? 'rotate(180deg)' : 'rotate(0deg)',
                                transition: 'transform 0.2s'
                              }}
                            />
                          </td>
                          <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{formatDateTime(session.started_at)}</td>
                          <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{session.patient_name}</td>
                          <td className="py-3" style={{ fontSize: '13px', color: '#5F5E5A' }}>{session.mrn}</td>
                          <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{session.patient_language}</td>
                          <td className="py-3">
                            {session.ats_category !== null ? (
                              <span
                                className="px-2 py-1"
                                style={{
                                  fontSize: '11px',
                                  borderRadius: '12px',
                                  backgroundColor: '#FFEBEE',
                                  color: '#C62828',
                                  fontWeight: 500
                                }}
                              >
                                ATS {session.ats_category}
                              </span>
                            ) : (
                              <span style={{ fontSize: '13px', color: '#5F5E5A' }}>—</span>
                            )}
                          </td>
                          <td className="py-3" style={{ fontSize: '13px', color: '#5F5E5A' }}>{formatDuration(session.duration_seconds)}</td>
                          <td className="py-3">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeleteTarget(session);
                                setShowDeleteModal(true);
                              }}
                              className="hover:underline"
                              style={{ fontSize: '13px', color: '#A32D2D' }}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                        {expandedRow === session.session_id && (
                          <tr style={{ borderBottom: '1px solid #E0DED6' }}>
                            <td colSpan={8} className="p-0">
                              <div className="p-6" style={{ backgroundColor: '#FAFBFC' }}>
                                <div className="grid grid-cols-2 gap-6">
                                  {/* Left: Transcript */}
                                  <div>
                                    <div className="flex items-center justify-between mb-4">
                                      <h4 style={{ fontSize: '14px', fontWeight: 500, color: '#1A1A1A' }}>Session transcript</h4>
                                      <button
                                        className="flex items-center gap-1.5 transition-opacity hover:opacity-80"
                                        style={{
                                          padding: '6px 12px',
                                          backgroundColor: '#185FA5',
                                          color: 'white',
                                          borderRadius: '6px',
                                          fontSize: '12px',
                                          fontWeight: 500
                                        }}
                                      >
                                        <Download size={14} />
                                        Export PDF
                                      </button>
                                    </div>
                                    {/* Transcript messages are loaded via a separate detail endpoint */}
                                    <p style={{ fontSize: '13px', color: '#5F5E5A' }}>Transcript not available in summary view.</p>
                                  </div>

                                  {/* Right: Summary */}
                                  <div>
                                    <h4 className="mb-4" style={{ fontSize: '14px', fontWeight: 500, color: '#1A1A1A' }}>Session summary</h4>
                                    <div className="space-y-3">
                                      <div>
                                        <div style={{ fontSize: '11px', fontWeight: 500, color: '#5F5E5A', marginBottom: '2px' }}>
                                          STARTED
                                        </div>
                                        <div style={{ fontSize: '13px', color: '#1A1A1A' }}>
                                          {formatDateTime(session.started_at)}
                                        </div>
                                      </div>
                                      <div>
                                        <div style={{ fontSize: '11px', fontWeight: 500, color: '#5F5E5A', marginBottom: '2px' }}>
                                          ENDED
                                        </div>
                                        <div style={{ fontSize: '13px', color: '#1A1A1A' }}>
                                          {session.ended_at ? formatDateTime(session.ended_at) : '—'}
                                        </div>
                                      </div>
                                      <div>
                                        <div style={{ fontSize: '11px', fontWeight: 500, color: '#5F5E5A', marginBottom: '2px' }}>
                                          DURATION
                                        </div>
                                        <div style={{ fontSize: '13px', color: '#1A1A1A' }}>
                                          {formatDuration(session.duration_seconds)}
                                        </div>
                                      </div>
                                      <div>
                                        <div style={{ fontSize: '11px', fontWeight: 500, color: '#5F5E5A', marginBottom: '2px' }}>
                                          AVG TRANSLATION CONFIDENCE
                                        </div>
                                        <div style={{ fontSize: '13px', color: '#1A1A1A' }}>
                                          {session.avg_translation_confidence !== null
                                            ? `${Math.round(session.avg_translation_confidence)}%`
                                            : '—'}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white" style={{ width: '440px', borderRadius: '12px', padding: '32px' }}>
            <h3 className="mb-3" style={{ fontSize: '16px', fontWeight: 500, color: '#1A1A1A' }}>
              Delete session record
            </h3>
            <p className="mb-6" style={{ fontSize: '13px', color: '#5F5E5A', lineHeight: '1.6' }}>
              This will permanently delete the session transcript for {deleteTarget.patient_name} ({formatDateTime(deleteTarget.started_at)}). This action is logged in the change log and cannot be undone.
            </p>

            {deleteError && (
              <p className="mb-4" style={{ fontSize: '12px', color: '#A32D2D' }}>{deleteError}</p>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleDeleteSession}
                disabled={isDeleting}
                className="flex-1 transition-opacity hover:opacity-90"
                style={{
                  height: '40px',
                  backgroundColor: '#A32D2D',
                  color: 'white',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 500,
                  opacity: isDeleting ? 0.7 : 1
                }}
              >
                {isDeleting ? 'Deleting…' : 'Delete record'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteTarget(null);
                  setDeleteError('');
                }}
                className="flex-1 transition-colors hover:bg-gray-50"
                style={{
                  height: '40px',
                  border: '1px solid #E0DED6',
                  borderRadius: '8px',
                  fontSize: '14px',
                  color: '#5F5E5A'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
