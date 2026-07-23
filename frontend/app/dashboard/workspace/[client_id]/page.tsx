"use client";

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { apiRequest } from '../../../api-client';
import TiptapEditor from '../../../components/TiptapEditor';

export default function WorkspacePage() {
  const params = useParams();
  const client_id = params.client_id as string;

  const [prompt, setPrompt] = useState('Generate the Q3 performance report');
  const [loading, setLoading] = useState(false);
  const [editorContent, setEditorContent] = useState<any>(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');

  const handleOrchestrate = async () => {
    setLoading(true);
    setError('');
    setSaveStatus('');
    try {
      const data = await apiRequest('/orchestrate', {
        method: 'POST',
        body: JSON.stringify({
          client_id: client_id,
          user_prompt: prompt
        })
      });
      if (data.status === 'success') {
        setEditorContent(data.tiptap_json);
      } else {
        setError(data.generated_system_prompt || 'Failed to orchestrate report.');
      }
    } catch (err: any) {
      setError(err.message || 'Connection failure.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editorContent) return;
    setSaveStatus('Saving...');
    setError('');
    try {
      const data = await apiRequest('/reports/save', {
        method: 'POST',
        body: JSON.stringify({
          client_id: client_id,
          report_name: `${client_id} Q3 Report`,
          tiptap_json: editorContent
        })
      });
      if (data.status === 'success') {
        setSaveStatus(`Saved report! Tracking ID: ${data.report_id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save report.');
      setSaveStatus('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px' }}>Split Canvas Workspace</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Client: <strong style={{ color: 'var(--color-teal)' }}>{client_id}</strong></p>
      </div>

      {error && (
        <div style={{ color: 'var(--color-alert)', background: 'hsla(342, 85%, 60%, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid hsla(342, 85%, 60%, 0.2)', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {/* Side-by-side editing split canvas */}
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>

        {/* Left Control Panel */}
        <div className="glass-card" style={{ flex: '1 1 350px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Report Directives</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>User Prompt Instruction</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="glass-input"
              rows={4}
              style={{ width: '100%', resize: 'none', fontSize: '14px', lineHeight: '1.5' }}
            />
          </div>
          <button onClick={handleOrchestrate} className="btn-primary" disabled={loading}>
            {loading ? 'Compiling Loop...' : 'Generate Report Blueprint'}
          </button>
        </div>

        {/* Right Canvas Panel */}
        <div style={{ flex: '2 1 600px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Tiptap Editable Sheet</h3>
            {editorContent && (
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                {saveStatus && <span style={{ fontSize: '13px', color: 'var(--color-teal)' }}>{saveStatus}</span>}
                <button onClick={handleSave} className="btn-primary" style={{ padding: '8px 16px', fontSize: '13px' }}>
                  Save Canvas
                </button>
              </div>
            )}
          </div>

          {editorContent ? (
            <TiptapEditor content={editorContent} onChange={setEditorContent} />
          ) : (
            <div className="glass-card" style={{ minHeight: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderStyle: 'dashed' }}>
              <p style={{ color: 'var(--text-muted)' }}>Enter directives and click Generate to load editable sheet.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
