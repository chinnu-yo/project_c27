"use client";

import { useWorkspaceStore } from '../store';
import SearchBox from '../components/SearchBox';

export default function DashboardHubPage() {
  const { clientId } = useWorkspaceStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '40px' }}>
      <div>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px' }}>
          Welcome Back
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Manage integrations, query records, and approve system preferences.
        </p>
      </div>

      {/* Global Search Command Bar Widget */}
      <div className="glass-card" style={{ padding: '32px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>
          Global Cross-App Search
        </h3>
        <SearchBox />
      </div>

      {/* Analytics telemetry metrics display grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
        <div className="glass-card" style={{ borderLeft: '4px solid var(--color-teal)' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Client</span>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px', color: 'var(--color-teal)' }}>{clientId}</h2>
        </div>

        <div className="glass-card" style={{ borderLeft: '4px solid var(--color-gemini)' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Database Mode</span>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px' }}>SQLite Local</h2>
        </div>

        <div className="glass-card" style={{ borderLeft: '4px solid var(--color-gemini)' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Vector Storage</span>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginTop: '8px' }}>Chroma Offline</h2>
        </div>
      </div>
    </div>
  );
}
