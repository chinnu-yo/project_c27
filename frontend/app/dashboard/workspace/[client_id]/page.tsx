"use client";

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { apiRequest } from '../../../api-client';
import TiptapEditor from '../../../components/TiptapEditor';

interface TemplateOption {
  template_id: string;
  template_name: string;
  description: string;
  file_type: string;
}

export default function WorkspacePage() {
  const params = useParams();
  const client_id = params.client_id as string;

  const [prompt, setPrompt] = useState('Generate the Q3 performance report');
  const [loading, setLoading] = useState(false);
  const [editorContent, setEditorContent] = useState<any>(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');

  // Templates selection state
  const [templates, setTemplates] = useState<TemplateOption[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  useEffect(() => {
    const fetchClientTemplates = async () => {
      if (!client_id) return;
      setLoadingTemplates(true);
      try {
        const data = await apiRequest(`/templates/list?client_id=${encodeURIComponent(client_id)}`);
        if (data.status === 'success' && Array.isArray(data.templates)) {
          setTemplates(data.templates);
          if (data.templates.length > 0) {
            setSelectedTemplateId(data.templates[0].template_id);
          }
        }
      } catch (err) {
        // Fallback silently if fetching templates fails
      } finally {
        setLoadingTemplates(false);
      }
    };

    fetchClientTemplates();
  }, [client_id]);

  const handleOrchestrate = async () => {
    setLoading(true);
    setError('');
    setSaveStatus('');
    try {
      const payload: any = {
        client_id: client_id,
        user_prompt: prompt
      };
      if (selectedTemplateId) {
        payload.template_id = selectedTemplateId;
      }

      const data = await apiRequest('/orchestrate', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (data && data.status === 'success' && data.tiptap_json) {
        setEditorContent(data.tiptap_json);
      } else {
        setEditorContent(null);
        setError(`⚠️ Report Generation Failed: ${data?.message || data?.detail || JSON.stringify(data)}`);
      }
    } catch (err: any) {
      setEditorContent(null);
      setError(`⚠️ Report Generation Failed: ${err.message || String(err)}`);
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

  const handleDownloadPDF = async () => {
    const element = document.getElementById('tiptap-print-container');
    if (!element) return;

    try {
      // Dynamically import html2pdf.js for client-side PDF rendering
      // @ts-ignore
      const html2pdfModule = await import('html2pdf.js');
      const html2pdf = (html2pdfModule.default || html2pdfModule) as any;
      const opt = {
        margin: 12,
        filename: `${client_id}_Executive_Report.pdf`,
        image: { type: 'jpeg' as const, quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'portrait' as const }
      };
      html2pdf().set(opt).from(element).save();
    } catch (err) {
      // Fallback print window if library environment fails
      window.print();
    }
  };

  const activeSelectedTemplate = templates.find(t => t.template_id === selectedTemplateId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px' }}>Split Canvas Workspace</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Client: <strong style={{ color: 'var(--color-teal)' }}>{client_id}</strong></p>
      </div>

      {/* Side-by-side editing split canvas */}
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>

        {/* Left Control Panel */}
        <div className="glass-card" style={{ flex: '1 1 350px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Report Directives</h3>

          {/* Template Picker */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Document Template Selection
            </label>
            <select
              value={selectedTemplateId}
              onChange={(e) => setSelectedTemplateId(e.target.value)}
              className="glass-input"
              style={{ width: '100%', padding: '10px 12px', fontSize: '14px', backgroundColor: 'var(--bg-card)' }}
            >
              <option value="">-- Default Executive Blueprint --</option>
              {templates.map((t) => (
                <option key={t.template_id} value={t.template_id}>
                  {t.template_name} (.{t.file_type})
                </option>
              ))}
            </select>
            {activeSelectedTemplate && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '6px', marginTop: '4px' }}>
                <strong style={{ color: 'var(--color-teal)' }}>Template Directive:</strong> {activeSelectedTemplate.description}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
              User Prompt Instruction
            </label>
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
                <button onClick={handleDownloadPDF} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '13px', color: 'var(--color-teal)', borderColor: 'var(--color-teal)' }}>
                  Download PDF
                </button>
                <button onClick={handleSave} className="btn-primary" style={{ padding: '8px 16px', fontSize: '13px' }}>
                  Save Canvas
                </button>
              </div>
            )}
          </div>

          {/* Red Error Box Displayed Directly on Workspace Canvas */}
          {error && (
            <div className="glass-card" style={{
              padding: '16px 20px',
              borderRadius: '12px',
              borderLeft: '4px solid #ef4444',
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              color: '#fca5a5',
              fontSize: '14px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              {error}
            </div>
          )}

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
