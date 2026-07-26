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
  const { clientId, userRole } = useWorkspaceStore();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; message: string; details: string; status: string } | null>(null);

  // Form states per provider
  const [geminiKey, setGeminiKey] = useState('');
  const [mongoUri, setMongoUri] = useState('');
  const [hubspotToken, setHubspotToken] = useState('');
  const [qbClientId, setQbClientId] = useState('');
  const [qbSecret, setQbSecret] = useState('');

  const isAdmin = userRole === 'Admin';

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiRequest<{ integrations: Integration[] }>(
        `/integrations/list?client_id=${clientId}`
      );
      setIntegrations(res.integrations || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load tenant integrations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (clientId) {
      fetchIntegrations();
    }
  }, [clientId]);

  const findIntegration = (name: string) => {
    return integrations.find(i => i.integration_name.toLowerCase().includes(name.toLowerCase()));
  };

  const handleSaveProvider = async (
    providerName: string,
    providerType: string,
    endpointUrl: string,
    secretCredential: string
  ) => {
    if (!isAdmin) {
      setError('Access Restricted: Admin privileges required to update integration credentials.');
      return;
    }

    if (!secretCredential) {
      setError(`Please enter a valid key or credential for ${providerName}.`);
      return;
    }

    try {
      setSavingProvider(providerName);
      setError(null);
      setSuccess(null);
      await apiRequest('/integrations', {
        method: 'POST',
        body: JSON.stringify({
          client_id: clientId,
          integration_name: providerName,
          integration_type: providerType,
          endpoint_url: endpointUrl,
          credential: secretCredential
        })
      });

      setSuccess(`Successfully updated ${providerName} integration for ${clientId}.`);
      
      // Reset sensitive input fields
      if (providerName.includes('Gemini')) setGeminiKey('');
      if (providerName.includes('MongoDB')) setMongoUri('');
      if (providerName.includes('HubSpot')) setHubspotToken('');
      if (providerName.includes('QuickBooks')) { setQbClientId(''); setQbSecret(''); }

      await fetchIntegrations();
    } catch (err: any) {
      setError(err.message || `Failed to save ${providerName} credentials.`);
    } finally {
      setSavingProvider(null);
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

  const geminiInteg = findIntegration('Gemini');
  const mongoInteg = findIntegration('MongoDB');
  const hubspotInteg = findIntegration('HubSpot');
  const qbInteg = findIntegration('QuickBooks');

  const renderBadge = (integ?: Integration) => {
    const isConnected = integ && integ.last_test_status.toLowerCase() === 'connected';
    const statusText = integ ? integ.last_test_status : 'Not Configured';

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 12px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 600,
        backgroundColor: isConnected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
        color: isConnected ? '#4ade80' : '#fca5a5'
      }}>
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: isConnected ? '#22c55e' : '#ef4444'
        }} />
        {statusText}
      </span>
    );
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          Integrations Settings & Provider Hub
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Manage client-isolated credentials and API tokens. All secret keys are Fernet-encrypted at rest for tenant <strong style={{ color: 'var(--text-primary)' }}>{clientId}</strong>.
        </p>
      </div>

      {/* RBAC Restriction Notice for Non-Admins */}
      {!isAdmin && (
        <div className="glass-card" style={{ padding: '16px 20px', borderRadius: '12px', borderLeft: '4px solid #eab308', backgroundColor: 'rgba(234, 179, 8, 0.1)' }}>
          <span style={{ color: '#fde047', fontSize: '14px', fontWeight: 600 }}>
            🔒 Access Restricted: You are currently logged in with a Member role. Only workspace Administrators can view secret tokens or save integration settings.
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

      {loading ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Loading integrations hub...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          
          {/* Card 1: Gemini AI API Key */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  🤖 Gemini AI API Key
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Powers Google Gemini report generation & cross-app search synthesis.
                </p>
              </div>
              {renderBadge(geminiInteg)}
            </div>

            {geminiInteg && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Active Secret: <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{geminiInteg.masked_credential}</span>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                API Secret Key
              </label>
              <input
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="glass-input"
                disabled={!isAdmin}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              {geminiInteg ? (
                <button
                  onClick={() => handleTestConnection(geminiInteg.id)}
                  disabled={testingId === geminiInteg.id}
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '12px', borderRadius: '6px' }}
                >
                  {testingId === geminiInteg.id ? 'Testing...' : 'Test Connection'}
                </button>
              ) : <div />}

              <button
                onClick={() => handleSaveProvider('Gemini AI', 'api_key', 'https://generativelanguage.googleapis.com/v1beta', geminiKey)}
                disabled={!isAdmin || savingProvider === 'Gemini AI'}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '6px' }}
              >
                {savingProvider === 'Gemini AI' ? 'Saving...' : 'Save Gemini Key'}
              </button>
            </div>

            {testResult?.id && geminiInteg?.id && testResult.id === geminiInteg.id && testResult?.message && (
              <div style={{ padding: '10px', borderRadius: '8px', fontSize: '12px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                {testResult.message}: {testResult?.details}
              </div>
            )}
          </div>

          {/* Card 2: MongoDB Atlas URI */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  🍃 MongoDB Atlas URI
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Connection string for vault templates and CRM document repositories.
                </p>
              </div>
              {renderBadge(mongoInteg)}
            </div>

            {mongoInteg && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Active Connection: <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{mongoInteg.masked_credential}</span>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                MongoDB Connection String
              </label>
              <input
                type="password"
                placeholder="mongodb+srv://user:pass@cluster.mongodb.net/dbname"
                value={mongoUri}
                onChange={(e) => setMongoUri(e.target.value)}
                className="glass-input"
                disabled={!isAdmin}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              {mongoInteg ? (
                <button
                  onClick={() => handleTestConnection(mongoInteg.id)}
                  disabled={testingId === mongoInteg.id}
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '12px', borderRadius: '6px' }}
                >
                  {testingId === mongoInteg.id ? 'Testing...' : 'Test Connection'}
                </button>
              ) : <div />}

              <button
                onClick={() => handleSaveProvider('MongoDB Atlas', 'connection_string', 'mongodb+srv://cluster.mongodb.net', mongoUri)}
                disabled={!isAdmin || savingProvider === 'MongoDB Atlas'}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '6px' }}
              >
                {savingProvider === 'MongoDB Atlas' ? 'Saving...' : 'Save Mongo URI'}
              </button>
            </div>

            {testResult?.id && mongoInteg?.id && testResult.id === mongoInteg.id && testResult?.message && (
              <div style={{ padding: '10px', borderRadius: '8px', fontSize: '12px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                {testResult.message}: {testResult?.details}
              </div>
            )}
          </div>

          {/* Card 3: HubSpot Private App Token */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  🟧 HubSpot Private App Token
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Private Access Token for active deals pipeline & lead stage sync.
                </p>
              </div>
              {renderBadge(hubspotInteg)}
            </div>

            {hubspotInteg && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Active Token: <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{hubspotInteg.masked_credential}</span>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                Private App Token
              </label>
              <input
                type="password"
                placeholder="pat-na1-..."
                value={hubspotToken}
                onChange={(e) => setHubspotToken(e.target.value)}
                className="glass-input"
                disabled={!isAdmin}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              {hubspotInteg ? (
                <button
                  onClick={() => handleTestConnection(hubspotInteg.id)}
                  disabled={testingId === hubspotInteg.id}
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '12px', borderRadius: '6px' }}
                >
                  {testingId === hubspotInteg.id ? 'Testing...' : 'Test Connection'}
                </button>
              ) : <div />}

              <button
                onClick={() => handleSaveProvider('HubSpot CRM', 'api_key', 'https://api.hubapi.com', hubspotToken)}
                disabled={!isAdmin || savingProvider === 'HubSpot CRM'}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '6px' }}
              >
                {savingProvider === 'HubSpot CRM' ? 'Connecting...' : 'Connect HubSpot'}
              </button>
            </div>

            {testResult?.id && hubspotInteg?.id && testResult.id === hubspotInteg.id && testResult?.message && (
              <div style={{ padding: '10px', borderRadius: '8px', fontSize: '12px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                {testResult.message}: {testResult?.details}
              </div>
            )}
          </div>

          {/* Card 4: QuickBooks Client Credentials */}
          <div className="glass-card" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  🧾 QuickBooks Credentials
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  OAuth Client ID & Client Secret for QuickBooks invoice sync.
                </p>
              </div>
              {renderBadge(qbInteg)}
            </div>

            {qbInteg && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Active Credentials: <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{qbInteg.masked_credential}</span>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Client ID
                </label>
                <input
                  type="text"
                  placeholder="AB123456..."
                  value={qbClientId}
                  onChange={(e) => setQbClientId(e.target.value)}
                  className="glass-input"
                  disabled={!isAdmin}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Client Secret
                </label>
                <input
                  type="password"
                  placeholder="Secret Key"
                  value={qbSecret}
                  onChange={(e) => setQbSecret(e.target.value)}
                  className="glass-input"
                  disabled={!isAdmin}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              {qbInteg ? (
                <button
                  onClick={() => handleTestConnection(qbInteg.id)}
                  disabled={testingId === qbInteg.id}
                  className="btn-secondary"
                  style={{ padding: '8px 14px', fontSize: '12px', borderRadius: '6px' }}
                >
                  {testingId === qbInteg.id ? 'Testing...' : 'Test Connection'}
                </button>
              ) : <div />}

              <button
                onClick={() => handleSaveProvider('QuickBooks Online', 'oauth', 'https://quickbooks.api.intuit.com', `${qbClientId}:${qbSecret}`)}
                disabled={!isAdmin || savingProvider === 'QuickBooks Online'}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '6px' }}
              >
                {savingProvider === 'QuickBooks Online' ? 'Saving...' : 'Save QuickBooks Credentials'}
              </button>
            </div>

            {testResult?.id && qbInteg?.id && testResult.id === qbInteg.id && testResult?.message && (
              <div style={{ padding: '10px', borderRadius: '8px', fontSize: '12px', backgroundColor: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)' }}>
                {testResult.message}: {testResult?.details}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
