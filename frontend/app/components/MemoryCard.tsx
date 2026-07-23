"use client";

import { useState } from 'react';

interface MemoryCardProps {
  id: string;
  extractedFact: string;
  message: string;
  domain: string;
  onAction: (id: string, action: 'approve' | 'reject') => Promise<void>;
}

export default function MemoryCard({ id, extractedFact, message, domain, onAction }: MemoryCardProps) {
  const [loadingAction, setLoadingAction] = useState<'approve' | 'reject' | null>(null);

  const handleAction = async (action: 'approve' | 'reject') => {
    setLoadingAction(action);
    try {
      await onAction(id, action);
    } catch (err) {
      // Error is caught and surfaced in the parent page container
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{
          fontSize: '11px',
          fontWeight: 600,
          color: 'var(--color-teal)',
          background: 'hsla(174, 75%, 45%, 0.1)',
          padding: '4px 10px',
          borderRadius: '12px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          {domain.replace('_', ' ')}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Pending Human Signoff</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', lineHeight: '1.4' }}>
          {message}
        </h4>
        <p style={{
          fontSize: '14px',
          color: 'var(--text-secondary)',
          background: 'hsla(224, 20%, 5%, 0.5)',
          padding: '12px',
          borderRadius: '8px',
          borderLeft: '3px solid var(--color-gemini)',
          fontStyle: 'italic'
        }}>
          "{extractedFact}"
        </p>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
        <button
          onClick={() => handleAction('approve')}
          className="btn-primary"
          style={{ flexGrow: 1, padding: '10px 16px', fontSize: '13px' }}
          disabled={loadingAction !== null}
        >
          {loadingAction === 'approve' ? 'Approving...' : 'Approve Preference'}
        </button>
        <button
          onClick={() => handleAction('reject')}
          className="btn-secondary"
          style={{ flexGrow: 1, padding: '10px 16px', fontSize: '13px', color: 'var(--color-alert)' }}
          disabled={loadingAction !== null}
        >
          {loadingAction === 'reject' ? 'Rejecting...' : 'Reject'}
        </button>
      </div>
    </div>
  );
}
