'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { FullDocumentEditor } from '@/components/documents/FullDocumentEditor';
import { useDocuments } from '@/hooks/use-documents';
import { useToast } from '@/hooks/use-toast';
import api from '@/lib/api';

export default function DocumentEditPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;
  const { toast } = useToast();

  const { useDocument } = useDocuments();
  const { data: documentData, isLoading, error } = useDocument(documentId);

  const [htmlContent, setHtmlContent] = useState<string | null>(null);

  // Extract body content from full HTML
  useEffect(() => {
    if (documentData?.generated_html) {
      const bodyMatch = documentData.generated_html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
      setHtmlContent(bodyMatch?.[1]?.trim() || documentData.generated_html);
    } else if (documentData?.markdown_content) {
      // Fallback: use markdown wrapped in basic HTML
      setHtmlContent(documentData.markdown_content);
    }
  }, [documentData?.generated_html, documentData?.markdown_content]);

  // Save handler
  const handleSave = useCallback(
    async (content: string) => {
      await api.patch(`/api/v1/documents/items/${documentId}/`, {
        generated_html: content,
      });
    },
    [documentId]
  );

  // Export PDF handler
  const handleExportPdf = useCallback(async () => {
    const baseUrl = /^https?:\/\//.test(process.env.NEXT_PUBLIC_API_URL || '')
      ? process.env.NEXT_PUBLIC_API_URL!
      : '';
    const response = await fetch(
      `${baseUrl}/api/v1/documents/items/${documentId}/export_pdf/`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      }
    );

    if (!response.ok) throw new Error('Falha ao gerar PDF');

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${documentData?.title || 'documento'}.pdf`;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);

    toast({ title: 'PDF gerado', description: 'Download iniciado.' });
  }, [documentId, documentData?.title, toast]);

  // Close handler
  const handleClose = useCallback(() => {
    router.push(`/dashboard/documents/${documentId}`);
  }, [router, documentId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !documentData) {
    return (
      <div className="flex items-center justify-center min-h-screen text-muted-foreground">
        Documento nao encontrado.
      </div>
    );
  }

  if (htmlContent === null) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <FullDocumentEditor
      content={htmlContent}
      title={documentData.title || 'Documento'}
      documentId={documentId}
      onSave={handleSave}
      onExportPdf={handleExportPdf}
      onClose={handleClose}
      autoSave
      autoSaveInterval={30000}
    />
  );
}
