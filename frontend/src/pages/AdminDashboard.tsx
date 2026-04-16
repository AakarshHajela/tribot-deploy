import { useState, useEffect } from 'react';
import { Search, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router';
import { logout } from '../api/authApi';
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  deactivateUser,
  reactivateUser,
} from '../api/adminApi';
import type { AdminUser, CreateUserPayload, UpdateUserPayload } from '../types';

function formatLastLogin(iso: string | null): string {
  if (!iso) return 'Never';
  return new Date(iso).toLocaleString('en-AU', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function AdminDashboard() {
  const navigate = useNavigate();

  // ── Data state ──
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // ── Add user modal ──
  const [showAddModal, setShowAddModal] = useState(false);
  const [newFullName, setNewFullName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'clinician'>('clinician');
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [addError, setAddError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ── Edit user modal ──
  const [editTarget, setEditTarget] = useState<AdminUser | null>(null);
  const [editFullName, setEditFullName] = useState('');
  const [editRole, setEditRole] = useState<'admin' | 'clinician'>('clinician');
  const [editError, setEditError] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // ── Delete modal ──
  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  // ── Fetch users ──
  useEffect(() => {
    setIsLoading(true);
    setError('');
    listUsers({ search: searchQuery || undefined })
      .then((res) => setUsers(res.items))
      .catch((err: Error) => setError(err.message || 'Could not load users.'))
      .finally(() => setIsLoading(false));
  }, [searchQuery]);

  const handleLogout = () => {
    logout();
  };

  // ── Create user ──
  const handleCreateUser = () => {
    if (!newFullName.trim() || !newEmail.trim()) {
      setAddError('Full name and email are required.');
      return;
    }
    setIsSubmitting(true);
    setAddError('');
    const payload: CreateUserPayload = { full_name: newFullName.trim(), email: newEmail.trim(), role: newRole };
    createUser(payload)
      .then((res) => {
        setTempPassword(res.temporary_password);
        setUsers((prev) => [res.user, ...prev]);
      })
      .catch((err: Error) => setAddError(err.message || 'Could not create user.'))
      .finally(() => setIsSubmitting(false));
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
    setNewFullName('');
    setNewEmail('');
    setNewRole('clinician');
    setTempPassword(null);
    setAddError('');
  };

  // ── Edit user ──
  const openEditModal = (user: AdminUser) => {
    setEditTarget(user);
    setEditFullName(user.full_name ?? '');
    setEditRole(user.role);
    setEditError('');
  };

  const handleUpdateUser = () => {
    if (!editTarget) return;
    setIsEditing(true);
    setEditError('');
    const payload: UpdateUserPayload = { full_name: editFullName.trim() || undefined, role: editRole };
    updateUser(editTarget.id, payload)
      .then((updated) => {
        setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
        setEditTarget(null);
      })
      .catch((err: Error) => setEditError(err.message || 'Could not update user.'))
      .finally(() => setIsEditing(false));
  };

  // ── Delete user ──
  const handleDeleteUser = () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    setDeleteError('');
    deleteUser(deleteTarget.id)
      .then(() => {
        setUsers((prev) => prev.filter((u) => u.id !== deleteTarget.id));
        setShowDeleteModal(false);
        setDeleteTarget(null);
      })
      .catch((err: Error) => setDeleteError(err.message || 'Could not delete user.'))
      .finally(() => setIsDeleting(false));
  };

  // ── Deactivate / reactivate ──
  const handleToggleActive = (user: AdminUser) => {
    const action = user.is_active ? deactivateUser : reactivateUser;
    action(user.id)
      .then((updated) => setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u))))
      .catch((err: Error) => setError(err.message || 'Could not update user status.'));
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
                  color: '#185FA5',
                  fontWeight: 500
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
            Loading users…
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center text-[13px] text-[#A32D2D] py-20">
            {error}
          </div>
        ) : (
          <div className="bg-white" style={{ borderRadius: '12px', border: '0.5px solid #E0DED6', padding: '32px' }}>
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: 500, color: '#1A1A1A', marginBottom: '4px' }}>
                  User management
                </h2>
                <p style={{ fontSize: '13px', color: '#5F5E5A' }}>
                  Manage clinician accounts and access permissions
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(true)}
                className="transition-opacity hover:opacity-90"
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#185FA5',
                  color: 'white',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 500
                }}
              >
                + Add user
              </button>
            </div>

            {/* Search Bar */}
            <div className="mb-6 relative" style={{ width: '40%' }}>
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#5F5E5A' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search users by name or email..."
                className="w-full outline-none pl-10"
                style={{
                  height: '40px',
                  border: '1px solid #E0DED6',
                  borderRadius: '8px',
                  fontSize: '13px',
                  color: '#1A1A1A',
                  paddingRight: '12px'
                }}
              />
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: '1px solid #E0DED6' }}>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Name</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Email</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Role</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Status</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Last login</th>
                    <th className="text-left pb-3 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A', fontWeight: 500 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user, idx) => (
                    <tr key={user.id} style={{ borderBottom: idx < users.length - 1 ? '1px solid #E0DED6' : 'none' }}>
                      <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{user.full_name ?? '—'}</td>
                      <td className="py-3" style={{ fontSize: '13px', color: '#5F5E5A' }}>{user.email}</td>
                      <td className="py-3" style={{ fontSize: '13px', color: '#1A1A1A' }}>{user.role.charAt(0).toUpperCase() + user.role.slice(1)}</td>
                      <td className="py-3">
                        <span
                          className="px-2 py-1"
                          style={{
                            fontSize: '11px',
                            borderRadius: '12px',
                            backgroundColor: user.is_active ? '#E8F5E9' : '#F5F5F5',
                            color: user.is_active ? '#2E7D32' : '#757575',
                            fontWeight: 500
                          }}
                        >
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3" style={{ fontSize: '13px', color: '#5F5E5A' }}>{formatLastLogin(user.last_login)}</td>
                      <td className="py-3">
                        <div className="flex gap-3">
                          <button
                            className="hover:underline"
                            style={{ fontSize: '13px', color: '#185FA5' }}
                            onClick={() => openEditModal(user)}
                          >
                            Edit
                          </button>
                          <button
                            className="hover:underline"
                            style={{
                              fontSize: '13px',
                              color: user.is_active ? '#BA7517' : '#3B6D11'
                            }}
                            onClick={() => handleToggleActive(user)}
                          >
                            {user.is_active ? 'Deactivate' : 'Reactivate'}
                          </button>
                          <button
                            className="hover:underline"
                            style={{ fontSize: '13px', color: '#A32D2D' }}
                            onClick={() => {
                              setDeleteTarget(user);
                              setShowDeleteModal(true);
                            }}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white" style={{ width: '480px', borderRadius: '12px', padding: '32px' }}>
            {tempPassword ? (
              <>
                <h3 className="mb-4" style={{ fontSize: '18px', fontWeight: 500, color: '#1A1A1A' }}>
                  User created
                </h3>
                <p className="mb-2" style={{ fontSize: '13px', color: '#5F5E5A', lineHeight: '1.6' }}>
                  Share this temporary password with the new user. It will not be shown again.
                </p>
                <div
                  className="mb-6 px-4 py-3 font-mono"
                  style={{
                    backgroundColor: '#F4F6F8',
                    border: '1px solid #E0DED6',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#1A1A1A',
                    letterSpacing: '0.05em'
                  }}
                >
                  {tempPassword}
                </div>
                <button
                  onClick={handleCloseAddModal}
                  className="w-full transition-opacity hover:opacity-90"
                  style={{
                    height: '40px',
                    backgroundColor: '#185FA5',
                    color: 'white',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: 500
                  }}
                >
                  Done
                </button>
              </>
            ) : (
              <>
                <h3 className="mb-6" style={{ fontSize: '18px', fontWeight: 500, color: '#1A1A1A' }}>
                  Add new user
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>Full name</label>
                    <input
                      type="text"
                      value={newFullName}
                      onChange={(e) => setNewFullName(e.target.value)}
                      className="w-full outline-none"
                      style={{
                        height: '40px',
                        padding: '0 12px',
                        border: '1px solid #E0DED6',
                        borderRadius: '8px',
                        fontSize: '13px'
                      }}
                    />
                  </div>

                  <div>
                    <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>Email address</label>
                    <input
                      type="email"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      className="w-full outline-none"
                      style={{
                        height: '40px',
                        padding: '0 12px',
                        border: '1px solid #E0DED6',
                        borderRadius: '8px',
                        fontSize: '13px'
                      }}
                    />
                  </div>

                  <div>
                    <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>Role</label>
                    <select
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value as 'admin' | 'clinician')}
                      className="w-full outline-none"
                      style={{
                        height: '40px',
                        padding: '0 12px',
                        border: '1px solid #E0DED6',
                        borderRadius: '8px',
                        fontSize: '13px'
                      }}
                    >
                      <option value="admin">Admin</option>
                      <option value="clinician">Clinician</option>
                    </select>
                  </div>

                  <p className="pt-2" style={{ fontSize: '11px', color: '#5F5E5A' }}>
                    Admins can manage users and view session history. Clinicians can translate and view session history.
                  </p>

                  {addError && (
                    <p style={{ fontSize: '12px', color: '#A32D2D' }}>{addError}</p>
                  )}

                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={handleCreateUser}
                      disabled={isSubmitting}
                      className="flex-1 transition-opacity hover:opacity-90"
                      style={{
                        height: '40px',
                        backgroundColor: '#185FA5',
                        color: 'white',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: 500,
                        opacity: isSubmitting ? 0.7 : 1
                      }}
                    >
                      {isSubmitting ? 'Creating…' : 'Send invitation'}
                    </button>
                    <button
                      onClick={handleCloseAddModal}
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
              </>
            )}
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white" style={{ width: '480px', borderRadius: '12px', padding: '32px' }}>
            {/* ===== BACK BUTTON ===== */}
            <button
              onClick={() => {
                setEditTarget(null);
                setEditError('');
              }}
              className="flex items-center gap-1 mb-4 hover:underline transition-colors"
              style={{ fontSize: '13px', color: '#5F5E5A' }}
            >
              ← Back
            </button>
            {/* ===== END BACK BUTTON ===== */}
            <h3 className="mb-6" style={{ fontSize: '18px', fontWeight: 500, color: '#1A1A1A' }}>
              Edit user
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>Full name</label>
                <input
                  type="text"
                  value={editFullName}
                  onChange={(e) => setEditFullName(e.target.value)}
                  className="w-full outline-none"
                  style={{
                    height: '40px',
                    padding: '0 12px',
                    border: '1px solid #E0DED6',
                    borderRadius: '8px',
                    fontSize: '13px'
                  }}
                />
              </div>

              <div>
                <label className="block mb-1 uppercase tracking-wide" style={{ fontSize: '11px', color: '#5F5E5A' }}>Role</label>
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value as 'admin' | 'clinician')}
                  className="w-full outline-none"
                  style={{
                    height: '40px',
                    padding: '0 12px',
                    border: '1px solid #E0DED6',
                    borderRadius: '8px',
                    fontSize: '13px'
                  }}
                >
                  <option value="admin">Admin</option>
                  <option value="clinician">Clinician</option>
                </select>
              </div>

              {editError && (
                <p style={{ fontSize: '12px', color: '#A32D2D' }}>{editError}</p>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleUpdateUser}
                  disabled={isEditing}
                  className="flex-1 transition-opacity hover:opacity-90"
                  style={{
                    height: '40px',
                    backgroundColor: '#185FA5',
                    color: 'white',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: 500,
                    opacity: isEditing ? 0.7 : 1
                  }}
                >
                  {isEditing ? 'Saving…' : 'Save changes'}
                </button>
                <button
                  onClick={() => setEditTarget(null)}
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
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white" style={{ width: '440px', borderRadius: '12px', padding: '32px' }}>
            <h3 className="mb-3" style={{ fontSize: '16px', fontWeight: 500, color: '#1A1A1A' }}>
              Delete user
            </h3>
            <p className="mb-6" style={{ fontSize: '13px', color: '#5F5E5A', lineHeight: '1.6' }}>
              This will remove {deleteTarget.full_name ?? deleteTarget.email} from the system. The account will be deactivated in the back end. This action is logged in the change log.
            </p>

            {deleteError && (
              <p className="mb-4" style={{ fontSize: '12px', color: '#A32D2D' }}>{deleteError}</p>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleDeleteUser}
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
                {isDeleting ? 'Deleting…' : 'Delete user'}
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
