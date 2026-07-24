"use client";

import { useState } from 'react';
import { useWorkspaceStore } from '../store';
import { apiRequest } from '../api-client';

export default function SearchBox() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ answer: string; sources: string[] } | null>(null);
  const [error, setError] = useState('');

  const { clientId } = useWorkspaceStore();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await apiRequest('/search', {
        method: 'POST',
        body: JSON.stringify({
          client_id: clientId,
          query_string: query,
          query: query
        })
      });
      setResult({
        answer: data.answer,
        sources: data.sources_consulted || []
      });
    } catch (err: any) {
      setError(err.message || 'Failed to complete search query.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask system workspace (e.g. What is Q3 traffic vs invoices?)"
          className="glass-input"
          style={{ flexGrow: 1, padding: '14px 20px', fontSize: '15px' }}
          disabled={loading}
        />
        <button type="submit" className="btn-primary" disabled={loading} style={{ padding: '14px 28px' }}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && (
        <div style={{ color: 'var(--color-alert)', background: 'hsla(342, 85%, 60%, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid hsla(342, 85%, 60%, 0.2)', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {result && (
        <div className="glass-card" style={{
          background: 'linear-gradient(to right, hsla(262, 80%, 65%, 0.05), var(--bg-card))',
          borderLeft: '4px solid var(--color-gemini)',
          padding: '20px'
        }}>
          <h4 style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--color-gemini)', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Search Synthesis
          </h4>
          <p style={{ fontSize: '16px', lineHeight: '1.6', color: 'var(--text-primary)', marginBottom: '16px' }}>
            {result.answer}
          </p>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sources Consulted:</span>
            {result.sources.map((src) => (
              <span
                key={src}
                style={{
                  fontSize: '11px',
                  color: 'var(--color-teal)',
                  background: 'hsla(174, 75%, 45%, 0.1)',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: 500,
                  textTransform: 'uppercase'
                }}
              >
                {src}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
