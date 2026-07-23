"use client";

import { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';

interface TiptapEditorProps {
  content: any;
  onChange: (newContent: any) => void;
}

export default function TiptapEditor({ content, onChange }: TiptapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({ resizable: true }),
      TableRow,
      TableCell,
      TableHeader,
    ],
    content: content || { type: 'doc', content: [] },
    onUpdate: ({ editor }) => {
      onChange(editor.getJSON());
    },
  });

  // Synchronize dynamic updates from parent (e.g. AI generation updates)
  useEffect(() => {
    if (editor && content) {
      const currentJSON = JSON.stringify(editor.getJSON());
      const newJSON = JSON.stringify(content);
      if (currentJSON !== newJSON) {
        editor.commands.setContent(content, false);
      }
    }
  }, [content, editor]);

  if (!editor) {
    return <div style={{ color: 'var(--text-secondary)' }}>Loading editor canvas...</div>;
  }

  return (
    <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Editor toolbar */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px' }}>
        <button onClick={() => editor.chain().focus().toggleBold().run()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
          Bold
        </button>
        <button onClick={() => editor.chain().focus().toggleItalic().run()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
          Italic
        </button>
        <button onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
          H1
        </button>
        <button onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
          H2
        </button>
        <button onClick={() => editor.chain().focus().toggleBulletList().run()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
          Bullet List
        </button>
        <button onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', color: 'var(--color-teal)' }}>
          Add Table
        </button>
      </div>

      {/* Editor text sheet container */}
      <div style={{ minHeight: '300px', outline: 'none' }}>
        <EditorContent editor={editor} style={{ outline: 'none', color: 'var(--text-primary)' }} />
      </div>
    </div>
  );
}
