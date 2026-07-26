"use client";

import React, { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../../store';
import { apiRequest } from '../../api-client';

interface Integration {
  id: string;
  client_id: string;
  integration_name: string;
  integration_type: string;
  endpoint_url: string;
  masked_credential: string;
  created_at: number;
  last_tested_at?: number;
  last_test_status: string;
}

export default function SettingsPage() {
  const { clientId } = useWorkspaceStore();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; message: string; details: string; status: string } | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [type, setType] = useState('api_key');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [credential, setCredential] = useState('');

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiRequest<{ integrations: Integration[] }>(
        `/integrations/list?client_id=${clientId}`
      );
      setIntegrations(res.integrations || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load integrations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (clientId) {
      fetchIntegrations();
    }
  }, [clientId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !endpointUrl || !credential) {
      setError('Please fill in all required integration fields.');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await apiRequest('/integrations', {
        method: 'POST',
        body: JSON.stringify({
          client_id: clientId,
          integration_name: name,
          integration_type: type,
          endpoint_url: endpointUrl,
          credential: credential
        })
      });

      // Clear secret field immediately
      setName('');
      setEndpointUrl('');
      setCredential('');
      await fetchIntegrations();
    } catch (err: any) {
      setError(err.message || 'Failed to save integration');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (integrationId: string) => {
    try {
      setTestingId(integrationId);
      setTestResult(null);
      const res = await apiRequest<{ status: string; message: string; verification_details: string }>(
        `/integrations/${integrationId}/test`,
        { method: 'POST' }
      );
      setTestResult({
        id: integrationId,
        status: res.status,
        message: res.message,
        details: res.verification_details
      });
      await fetchIntegrations();
    } catch (err: any) {
      setTestResult({
        id: integrationId,
        status: 'failed',
        message: 'Connection check error',
        details: err.message || 'Network failure during test request'
      });
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (integrationId: string) => {
    if (!confirm('Are you sure you want to remove this integration credentials entry?')) return;
    try {
      setError(null);
      await apiRequest(`/integrations/${integrationId}`, { method: 'DELETE' });
      await fetchIntegrations();
    } catch (err: any) {
      setError(err.message || 'Failed to delete integration');
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          Integrations Settings & Connections Hub
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Configure client-isolated integration endpoints, API keys, and connection strings. All secret credentials are Fernet-encrypted at rest.
        </p>
      </div>

      {error && (
        <div className="glass-card" style={{ padding: '16px', borderRadius: '12px', borderLeft: '4px solid #ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
          <span style={{ color: '#fca5a5', fontSize: '14px' }}>{error}</span>
        </div>
      )}

      {/* Connection Registration Form */}
      <div className="glass-card" style={{ padding: '28px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Add New Integration Connection
        </h2>

        <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
              Integration Name
            </label>
            <input
              type="text"
              placeholder="e.g. HubSpot Sales API, Client Postgres DB"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="glass-input"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '8px' }}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
              Credential Type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="glass-input"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)' }}
            >
              <option value="api_key">API Key / Token</option>
              <option value="connection_string">Database Connection String</option>
              <option value="oauth">OAuth Token</option>
            </select>
          </div>

          <div style={{ gridColumn: 'span 2' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
              Endpoint URL / Connection String
            </label>
            <input
              type="text"
              placeholder="e.g. https://api.hubspot.com/v3/deals or postgresql://user:pass@host:5432/dbname"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              className="glass-input"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '8px' }}
              required
            />
          </div>

          <div style={{ gridColumn: 'span 2' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase' }}>
              Secret Credential (Encrypted at rest)
            </label>
            <input
              type="password"
              placeholder="Enter secret key, token, or connection password"
              value={credential}
              onChange={(e) => setCredential(e.target.value)}
              className="glass-input"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '8px' }}
              required
            />
          </div>

          <div style={{ gridColumn: 'span 2', display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button
              type="submit"
              disabled={saving}
              className="btn-primary"
              style={{ padding: '12px 24px', borderRadius: '8px', fontWeight: 600 }}
            >
              {saving ? 'Encrypting & Saving...' : 'Save Integration'}
            </button>
          </div>
        </form>
      </div>

      {/* Integrations List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Configured Tenant Integrations ({integrations.length})
        </h2>

        {loading ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Loading integrations...</div>
        ) : integrations.length === 0 ? (
          <div className="glass-card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', borderRadius: '12px' }}>
            No integrations configured for {clientId} yet. Use the form above to store connection credentials.
          </div>
        ) : (
          integrations.map((item) => {
            const isTesting = testingId === item.id;
            const isConnected = item.last_test_status.toLowerCase() === 'connected';
            const isFailed = item.last_test_status.toLowerCase() === 'failed';
            const testInfo = testResult?.id === item.id ? testResult : null;

            return (
              <div
                key={item.id}
                className="glass-card"
                style={{
                  padding: '24px',
                  borderRadius: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  border: isConnected
                    ? '1px solid rgba(34, 197, 94, 0.3)'
                    : isFailed
                    ? '1px solid rgba(239, 68, 68, 0.3)'
                    : '1px solid var(--border-glass)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {item.integration_name}
                      </h3>
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        color: 'var(--text-secondary)',
                        textTransform: 'uppercase'
                      }}>
                        {item.integration_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'monospace' }}>
                      {item.endpoint_url}
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontSize: '12px',
                      fontWeight: 600,
                      backgroundColor: isConnected
                        ? 'rgba(34, 197, 94, 0.15)'
                        : isFailed
                        ? 'rgba(239, 68, 68, 0.15)'
                        : 'rgba(156, 163, 175, 0.15)',
                      color: isConnected
                        ? '#4ade80'
                        : isFailed
                        ? '#fca5a5'
                        : '#9ca3af'
                    }}>
                      <span style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: isConnected ? '#22c55e' : isFailed ? '#ef4444' : '#6b7280'
                      }} />
                      {item.last_test_status}
                    </span>
                  </div>
                </div>

                {/* Secret Mask representation & Controls */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border-glass)' }}>
                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    Stored Secret: <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)', fontWeight: 600 }}>{item.masked_credential}</span>
                  </div>

                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button
                      onClick={() => handleTestConnection(item.id)}
                      disabled={isTesting}
                      className="btn-secondary"
                      style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '6px' }}
                    >
                      {isTesting ? 'Testing Connectivity...' : 'Test Connection'}
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      style={{
                        padding: '8px 16px',
                        fontSize: '13px',
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
                </div>

                {/* Test details output */}
                {testInfo && (
                  <div style={{
                    marginTop: '8px',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    backgroundColor: testInfo.status === 'connected' ? 'rgba(34, 197, 94, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                    border: `1px solid ${testInfo.status === 'connected' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                  }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: testInfo.status === 'connected' ? '#4ade80' : '#fca5a5' }}>
                      {testInfo.message}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {testInfo.details}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
