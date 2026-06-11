'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { FullDocumentEditor } from '@/components/documents/FullDocumentEditor';
import api from '@/lib/api';

function EditorContent() {
  const searchParams = useSearchParams();
  const docId = searchParams.get('doc');
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');

  useEffect(() => {
    // Try sessionStorage first (from ResultPhase)
    const stored = sessionStorage.getItem('verus_editor_content');
    if (stored) {
      setContent(stored);
      setTitle(sessionStorage.getItem('verus_editor_title') || 'Documento');
      return;
    }
    // Fallback: load from API if docId
    if (docId) {
      api.get(`/api/v1/intelligent-assistant/documents/${docId}/`)
        .then(res => {
          setContent(res.data.html_content || res.data.markdown_content || '');
          setTitle(res.data.title || 'Documento');
        });
    }
  }, [docId]);

  if (!content) return <div className="flex items-center justify-center h-screen">Carregando editor...</div>;

  return (
    <FullDocumentEditor
      content={content}
      title={title}
      documentId={docId || undefined}
      onSave={async (html) => {
        if (docId) {
          await api.put(`/api/v1/intelligent-assistant/documents/${docId}/update-html/`, { html_content: html });
        }
      }}
      onExportPdf={async () => {
        if (!docId) return;
        const response = await api.post(
          `/api/v1/intelligent-assistant/documents/${docId}/generate-pdf/`,
          {},
          { responseType: 'blob', timeout: 120000 }
        );
        const blobUrl = URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `${title || 'documento'}.pdf`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
      }}
      onClose={() => window.close()}
    />
  );
}

export default function EditorPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen">Carregando...</div>}>
      <EditorContent />
    </Suspense>
  );
}
