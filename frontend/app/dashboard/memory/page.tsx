"use client";

import { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../../store';
import { apiRequest } from '../../api-client';
import MemoryCard from '../../components/MemoryCard';

interface NotificationItem {
  _id: string;
  client_id: string;
  message: string;
  extracted_fact: string;
  domain: string;
}

export default function MemoryPortalPage() {
  const { clientId } = useWorkspaceStore();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadNotifications = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiRequest(`/memory/pending?client_id=${clientId}`);
      setNotifications(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load notifications list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [clientId]);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    const item = notifications.find(n => n._id === id);
    if (!item) return;

    try {
      const data = await apiRequest('/memory/validate', {
        method: 'POST',
        body: JSON.stringify({
          notification_id: id,
          client_id: clientId,
          action: action,
          extracted_fact: item.extracted_fact,
          domain: item.domain
        })
      });
      if (data.status === 'success') {
        // Remove item from UI list on successful action
        setNotifications((prev) => prev.filter((n) => n._id !== id));
      }
    } catch (err: any) {
      setError(err.message || 'Verification transition failed.');
      throw err;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px' }}>Fact Validation Feed</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Human-in-the-loop validation log dashboard.</p>
      </div>

      {error && (
        <div style={{ color: 'var(--color-alert)', background: 'hsla(342, 85%, 60%, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid hsla(342, 85%, 60%, 0.2)', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ color: 'var(--text-muted)' }}>Loading validations list...</div>
      ) : notifications.length === 0 ? (
        <div className="glass-card" style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderStyle: 'dashed' }}>
          <p style={{ color: 'var(--text-muted)' }}>All client preferences are aligned. No items require validation.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          {notifications.map((notif) => (
            <MemoryCard
              key={notif._id}
              id={notif._id}
              extractedFact={notif.extracted_fact}
              message={notif.message}
              domain={notif.domain}
              onAction={handleAction}
            />
          ))}
        </div>
      )}
    </div>
  );
}
