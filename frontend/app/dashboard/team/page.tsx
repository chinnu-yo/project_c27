"use client";

import React, { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../../store';
import { apiRequest } from '../../api-client';

interface TeamMember {
  id: string;
  email: string;
  role: 'Admin' | 'Member';
  client_access: string[];
  status: 'active' | 'pending';
  created_at: number;
}

const AVAILABLE_CLIENTS = ['client_abc', 'client_xyz'];

export default function TeamPage() {
  const { clientId, userRole } = useWorkspaceStore();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isAdmin = userRole === 'Admin';

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePassword, setInvitePassword] = useState('');
  const [inviteRole, setInviteRole] = useState<'Admin' | 'Member'>('Member');
  const [inviteClients, setInviteClients] = useState<string[]>([clientId || 'client_abc']);
  const [inviting, setInviting] = useState(false);

  // Edit modal state
  const [editingMember, setEditingMember] = useState<TeamMember | null>(null);
  const [editRole, setEditRole] = useState<'Admin' | 'Member'>('Member');
  const [editClients, setEditClients] = useState<string[]>([]);
  const [updating, setUpdating] = useState(false);

  const fetchTeamMembers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiRequest<{ members: TeamMember[] }>(`/team/list?client_id=${clientId}`);
      setMembers(res.members || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (clientId) {
      fetchTeamMembers();
    }
  }, [clientId]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) {
      setError('Access Restricted: Admin privileges required to invite team members.');
      return;
    }
    if (!inviteEmail) {
      setError('Please enter a valid email address.');
      return;
    }

    try {
      setInviting(true);
      setError(null);
      await apiRequest('/team/invite', {
        method: 'POST',
        body: JSON.stringify({
          email: inviteEmail,
          password: invitePassword || 'password123',
          role: inviteRole,
          client_access: inviteClients
        })
      });

      setSuccess(`Account created for ${inviteEmail}`);
      setShowInviteModal(false);
      setInviteEmail('');
      setInvitePassword('');
      setInviteRole('Member');
      setInviteClients([clientId || 'client_abc']);
      await fetchTeamMembers();
    } catch (err: any) {
      setError(err.message || 'Failed to send invite');
    } finally {
      setInviting(false);
    }
  };

  const handleStartEdit = (member: TeamMember) => {
    if (!isAdmin) {
      setError('Access Restricted: Admin privileges required to edit team member permissions.');
      return;
    }
    setEditingMember(member);
    setEditRole(member.role);
    setEditClients(member.client_access || []);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMember || !isAdmin) return;

    try {
      setUpdating(true);
      setError(null);
      await apiRequest(`/team/${editingMember.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          role: editRole,
          client_access: editClients
        })
      });

      setSuccess(`Updated permissions for ${editingMember.email}`);
      setEditingMember(null);
      await fetchTeamMembers();
    } catch (err: any) {
      setError(err.message || 'Failed to update member permissions');
    } finally {
      setUpdating(false);
    }
  };

  const handleRemove = async (memberId: string, email: string) => {
    if (!isAdmin) {
      setError('Access Restricted: Admin privileges required to remove team members.');
      return;
    }
    if (!confirm(`Are you sure you want to remove team member ${email}?`)) return;
    try {
      setError(null);
      await apiRequest(`/team/${memberId}`, { method: 'DELETE' });
      setSuccess(`Removed team member ${email}`);
      await fetchTeamMembers();
    } catch (err: any) {
      setError(err.message || 'Failed to remove team member');
    }
  };

  const toggleClientAccess = (client: string, currentList: string[], setList: (val: string[]) => void) => {
    if (currentList.includes(client)) {
      setList(currentList.filter(c => c !== client));
    } else {
      setList([...currentList, client]);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header & Main Control */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
            Team & Access Management
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Manage team roles, pending invitations, and workspace authorization boundaries across clients.
          </p>
        </div>

        <button
          onClick={() => setShowInviteModal(true)}
          disabled={!isAdmin}
          className="btn-primary"
          style={{ padding: '12px 20px', borderRadius: '8px', fontWeight: 600, opacity: isAdmin ? 1 : 0.5, cursor: isAdmin ? 'pointer' : 'not-allowed' }}
        >
          + Invite Team Member
        </button>
      </div>

      {!isAdmin && (
        <div className="glass-card" style={{ padding: '16px 20px', borderRadius: '12px', borderLeft: '4px solid #eab308', backgroundColor: 'rgba(234, 179, 8, 0.1)' }}>
          <span style={{ color: '#fde047', fontSize: '14px', fontWeight: 600 }}>
            🔒 Access Restricted: You are currently logged in with a Member role. Only workspace Administrators can invite members or modify permissions.
          </span>
        </div>
      )}

      {error && (
        <div className="glass-card" style={{ padding: '16px', borderRadius: '12px', borderLeft: '4px solid #ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
          <span style={{ color: '#fca5a5', fontSize: '14px' }}>{error}</span>
        </div>
      )}

      {success && (
        <div className="glass-card" style={{ padding: '16px', borderRadius: '12px', borderLeft: '4px solid #22c55e', backgroundColor: 'rgba(34, 197, 94, 0.1)' }}>
          <span style={{ color: '#86efac', fontSize: '14px' }}>{success}</span>
        </div>
      )}

      {/* Team Members List Table */}
      <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Current Team Roster ({members.length})
        </h2>

        {loading ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Loading team members...</div>
        ) : members.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>No team members on record.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 16px' }}>Member Email</th>
                  <th style={{ padding: '12px 16px' }}>Role</th>
                  <th style={{ padding: '12px 16px' }}>Status</th>
                  <th style={{ padding: '12px 16px' }}>Client Access</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => {
                  const isAdmin = member.role === 'Admin';
                  const isPending = member.status === 'pending';

                  return (
                    <tr key={member.id} style={{ borderBottom: '1px solid var(--border-glass)', fontSize: '14px' }}>
                      <td style={{ padding: '16px', fontWeight: 500, color: 'var(--text-primary)' }}>
                        {member.email}
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 600,
                          backgroundColor: isAdmin ? 'rgba(168, 85, 247, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                          color: isAdmin ? '#c084fc' : '#93c5fd'
                        }}>
                          {member.role}
                        </span>
                      </td>
                      <td style={{ padding: '16px' }}>
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 600,
                          backgroundColor: isPending ? 'rgba(234, 179, 8, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                          color: isPending ? '#fde047' : '#4ade80'
                        }}>
                          {member.status.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '16px' }}>
                        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                          {member.client_access && member.client_access.length > 0 ? (
                            member.client_access.map(c => (
                              <span key={c} style={{
                                fontSize: '11px',
                                padding: '2px 8px',
                                borderRadius: '6px',
                                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                                color: 'var(--color-teal)'
                              }}>
                                {c}
                              </span>
                            ))
                          ) : (
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>None</span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '16px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          <button
                            onClick={() => handleStartEdit(member)}
                            className="btn-secondary"
                            style={{ padding: '6px 12px', fontSize: '12px', borderRadius: '6px' }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleRemove(member.id, member.email)}
                            style={{
                              padding: '6px 12px',
                              fontSize: '12px',
                              borderRadius: '6px',
                              backgroundColor: 'rgba(239, 68, 68, 0.1)',
                              color: '#ef4444',
                              border: '1px solid rgba(239, 68, 68, 0.2)',
                              cursor: 'pointer'
                            }}
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div className="glass-card" style={{ width: '480px', padding: '32px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Invite Team Member
            </h2>

            <form onSubmit={handleInvite} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Username / Email Address
                </label>
                <input
                  type="text"
                  placeholder="user@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="glass-input"
                  style={{ width: '100%', padding: '12px 16px', borderRadius: '8px' }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Initial Account Password
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={invitePassword}
                  onChange={(e) => setInvitePassword(e.target.value)}
                  className="glass-input"
                  style={{ width: '100%', padding: '12px 16px', borderRadius: '8px' }}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Role Assignment
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as any)}
                  className="glass-input"
                  style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)' }}
                >
                  <option value="Member">Member (Read / Edit canvas)</option>
                  <option value="Admin">Admin (Manage Team & Integrations)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
                  Client Workspace Access
                </label>
                <div style={{ display: 'flex', gap: '16px' }}>
                  {AVAILABLE_CLIENTS.map(c => (
                    <label key={c} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', color: 'var(--text-secondary)' }}>
                      <input
                        type="checkbox"
                        checked={inviteClients.includes(c)}
                        onChange={() => toggleClientAccess(c, inviteClients, setInviteClients)}
                      />
                      {c}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="btn-secondary"
                  style={{ padding: '10px 16px', borderRadius: '8px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviting}
                  className="btn-primary"
                  style={{ padding: '10px 20px', borderRadius: '8px', fontWeight: 600 }}
                >
                  {inviting ? 'Inviting...' : 'Create Pending Invite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Permissions Modal */}
      {editingMember && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div className="glass-card" style={{ width: '480px', padding: '32px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Edit Member Permissions
            </h2>

            <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              Member: <strong style={{ color: 'var(--text-primary)' }}>{editingMember.email}</strong>
            </div>

            <form onSubmit={handleSaveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Role Assignment
                </label>
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value as any)}
                  className="glass-input"
                  style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)' }}
                >
                  <option value="Member">Member (Read / Edit canvas)</option>
                  <option value="Admin">Admin (Manage Team & Integrations)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>
                  Client Workspace Access
                </label>
                <div style={{ display: 'flex', gap: '16px' }}>
                  {AVAILABLE_CLIENTS.map(c => (
                    <label key={c} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', color: 'var(--text-secondary)' }}>
                      <input
                        type="checkbox"
                        checked={editClients.includes(c)}
                        onChange={() => toggleClientAccess(c, editClients, setEditClients)}
                      />
                      {c}
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setEditingMember(null)}
                  className="btn-secondary"
                  style={{ padding: '10px 16px', borderRadius: '8px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updating}
                  className="btn-primary"
                  style={{ padding: '10px 20px', borderRadius: '8px', fontWeight: 600 }}
                >
                  {updating ? 'Saving...' : 'Save Permissions'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
