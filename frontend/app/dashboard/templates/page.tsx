"use client";

import { useState, useEffect } from 'react';
import { useWorkspaceStore } from '../../store';
import { apiRequest, downloadFileRequest } from '../../api-client';

interface TemplateMetadata {
  template_id: string;
  client_id: string;
  template_name: string;
  description: string;
  original_filename: string;
  file_type: string;
  uploaded_at: number;
}

export default function TemplatesPage() {
  const { clientId } = useWorkspaceStore();
  const [templates, setTemplates] = useState<TemplateMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form states
  const [templateName, setTemplateName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fetchTemplates = async () => {
    if (!clientId) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiRequest(`/templates/list?client_id=${encodeURIComponent(clientId)}`);
      if (data.status === 'success') {
        setTemplates(data.templates || []);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch templates list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, [clientId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext !== 'docx' && ext !== 'pptx') {
        setError('Only .docx and .pptx file formats are allowed.');
        setSelectedFile(null);
        return;
      }
      if (file.size > 15 * 1024 * 1024) {
        setError('File size exceeds maximum allowed limit of 15MB.');
        setSelectedFile(null);
        return;
      }
      setError('');
      setSelectedFile(file);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!templateName.trim()) {
      setError('Template Name is required.');
      return;
    }
    if (!description.trim()) {
      setError('Description is required ("why and where to use this template").');
      return;
    }
    if (!selectedFile) {
      setError('Please select a .docx or .pptx file to upload.');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('client_id', clientId);
      formData.append('template_name', templateName.trim());
      formData.append('description', description.trim());
      formData.append('file', selectedFile);

      const res = await apiRequest('/templates/upload', {
        method: 'POST',
        body: formData
      });

      if (res.status === 'success') {
        setSuccess(`Template '${res.template_name}' uploaded successfully!`);
        setTemplateName('');
        setDescription('');
        setSelectedFile(null);
        // Reset file input element
        const fileInput = document.getElementById('template-file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
        
        await fetchTemplates();
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (template: TemplateMetadata) => {
    setError('');
    try {
      const { blob, filename } = await downloadFileRequest(`/templates/download/${template.template_id}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || template.original_filename || `${template.template_id}.${template.file_type}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Failed to download template file.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px' }}>
          Client Document Templates
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload and manage custom document templates (.docx / .pptx) for client <strong style={{ color: 'var(--color-teal)' }}>{clientId}</strong>.
        </p>
      </div>

      {error && (
        <div style={{
          color: 'var(--color-alert)',
          background: 'hsla(342, 85%, 60%, 0.1)',
          padding: '12px 16px',
          borderRadius: '8px',
          border: '1px solid hsla(342, 85%, 60%, 0.2)',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          color: 'var(--color-teal)',
          background: 'hsla(170, 75%, 45%, 0.1)',
          padding: '12px 16px',
          borderRadius: '8px',
          border: '1px solid hsla(170, 75%, 45%, 0.2)',
          fontSize: '14px'
        }}>
          {success}
        </div>
      )}

      {/* Upload Form Card */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px' }}>
          Upload New Document Template
        </h2>

        <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Template Name *
              </label>
              <input
                type="text"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="e.g. Q3 Executive Presentation Blueprint"
                className="glass-input"
                required
                style={{ width: '100%', padding: '10px 14px', fontSize: '14px' }}
              />
            </div>

            <div style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Template File (.docx / .pptx) *
              </label>
              <input
                id="template-file-input"
                type="file"
                accept=".docx,.pptx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation"
                onChange={handleFileChange}
                className="glass-input"
                required
                style={{ width: '100%', padding: '8px 14px', fontSize: '14px' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
              Description ("Why and where to use this template") *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe when and where this template should be selected for report generation..."
              className="glass-input"
              rows={3}
              required
              style={{ width: '100%', padding: '10px 14px', fontSize: '14px', resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              className="btn-primary"
              disabled={uploading}
              style={{ padding: '10px 24px', fontSize: '14px' }}
            >
              {uploading ? 'Parsing & Uploading...' : 'Upload Template'}
            </button>
          </div>
        </form>
      </div>

      {/* Templates List Section */}
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px' }}>
          Stored Client Templates ({templates.length})
        </h2>

        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>Loading stored templates...</p>
        ) : templates.length === 0 ? (
          <div className="glass-card" style={{ padding: '32px', textAlign: 'center', borderStyle: 'dashed' }}>
            <p style={{ color: 'var(--text-muted)' }}>No templates uploaded for {clientId} yet. Upload a .docx or .pptx file above to get started.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {templates.map((tmpl) => (
              <div key={tmpl.template_id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {tmpl.template_name}
                    </h3>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {tmpl.original_filename}
                    </span>
                  </div>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    background: tmpl.file_type === 'docx' ? 'hsla(210, 80%, 55%, 0.2)' : 'hsla(25, 90%, 55%, 0.2)',
                    color: tmpl.file_type === 'docx' ? '#60a5fa' : '#fb923c',
                    border: tmpl.file_type === 'docx' ? '1px solid hsla(210, 80%, 55%, 0.3)' : '1px solid hsla(25, 90%, 55%, 0.3)'
                  }}>
                    .{tmpl.file_type}
                  </span>
                </div>

                <div style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  background: 'rgba(255,255,255,0.03)',
                  padding: '12px',
                  borderRadius: '8px',
                  lineHeight: '1.4'
                }}>
                  <strong style={{ color: 'var(--text-muted)', fontSize: '11px', display: 'block', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Usage Directives:
                  </strong>
                  {tmpl.description}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Uploaded {new Date(tmpl.uploaded_at * 1000).toLocaleDateString()}
                  </span>
                  <button
                    onClick={() => handleDownload(tmpl)}
                    className="btn-secondary"
                    style={{ padding: '6px 14px', fontSize: '12px' }}
                  >
                    Download File
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
