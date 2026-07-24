"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWorkspaceStore } from '../store';
import { apiRequest } from '../api-client';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [clientField, setClientField] = useState('client_abc');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const router = useRouter();
  const setClientId = useWorkspaceStore((state) => state.setClientId);
  const setJwtToken = useWorkspaceStore((state) => state.setJwtToken);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await apiRequest<{ access_token: string; token_type: string; client_id: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          client_id: clientField,
          password: password
        })
      });

      if (data && data.access_token) {
        setClientId(data.client_id || clientField);
        setJwtToken(data.access_token);
        router.push('/dashboard');
      } else {
        setError('Invalid credentials.');
      }
    } catch (err: any) {
      setError('Invalid credentials. Please check tenant client ID and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'radial-gradient(circle at top right, hsl(262, 40%, 12%), var(--bg-obsidian))'
    }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h2 style={{
            fontSize: '28px',
            fontWeight: 700,
            background: 'var(--color-gemini-gradient)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '8px'
          }}>
            Workspace Access
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            System of Action Gateway Portal
          </p>
        </div>

        {error && (
          <div style={{
            color: 'var(--color-alert)',
            fontSize: '14px',
            marginBottom: '16px',
            background: 'hsla(342, 85%, 60%, 0.1)',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid hsla(342, 85%, 60%, 0.2)'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
              Client Tenant ID
            </label>
            <select
              value={clientField}
              onChange={(e) => setClientField(e.target.value)}
              className="glass-input"
              style={{ width: '100%' }}
            >
              <option value="client_abc" style={{ backgroundColor: 'var(--bg-obsidian)' }}>client_abc (Boutique Agency)</option>
              <option value="client_xyz" style={{ backgroundColor: 'var(--bg-obsidian)' }}>client_xyz (Consultancy Group)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              className="glass-input"
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="glass-input"
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ width: '100%', marginTop: '12px', padding: '14px' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
