'use client';

import { use } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import Link from 'next/link';
import { useDocuments } from '@/hooks/use-documents';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Download, Printer, Loader2, FileText } from 'lucide-react';
import { PermissionGuard } from '@/components/auth/permission-guard';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function DocumentPreviewPage({ params }: PageProps) {
  const { id } = use(params);
  const { useDocument } = useDocuments();
  const { data: etp, isLoading } = useDocument(id);

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    if (!etp?.generated_html) return;

    const blob = new Blob([etp.generated_html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${etp.title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!etp) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <FileText className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Documento não encontrado</h3>
        <Link href="/dashboard/documents">
          <Button variant="outline">Voltar para lista</Button>
        </Link>
      </div>
    );
  }

  if (!etp.generated_html && !etp.generated_content) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard/documents/${id}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Documento não gerado</h3>
            <p className="text-sm text-muted-foreground mb-4 text-center">
              Este documento ainda não tem um conteúdo gerado. Volte e clique em "Gerar Documento".
            </p>
            <Link href={`/dashboard/documents/${id}`}>
              <Button>Voltar para Documento</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const documentHtml = etp.generated_html || etp.generated_content || '';

  return (
    <PermissionGuard anyPermission={['documents.edit_own', 'documents.edit_all']} redirectOnDeny redirectTo="/dashboard/documents">
    <div className="space-y-6">
      {/* Header - Hidden on print */}
      <div className="flex items-center justify-between print:hidden">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard/documents/${id}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{etp.title}</h1>
            <p className="text-sm text-muted-foreground">
              Preview do Documento Gerado
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download HTML
          </Button>
          <Button onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" />
            Imprimir
          </Button>
        </div>
      </div>

      {/* Document Preview */}
      <Card className="print:shadow-none print:border-none">
        <CardHeader className="print:hidden">
          <CardTitle>Documento Gerado</CardTitle>
        </CardHeader>
        <CardContent className="print:p-0">
          <div
            className="prose prose-sm max-w-none
              print:prose-sm
              bg-white text-black p-8 rounded-lg
              [&_h1]:text-black [&_h2]:text-black [&_h3]:text-black [&_h4]:text-black
              [&_p]:text-black [&_li]:text-black [&_strong]:text-black
              [&_td]:text-black [&_th]:text-black [&_a]:text-black
              [&_blockquote]:text-black [&_ul]:text-black [&_ol]:text-black
              [&_td]:border-border [&_th]:border-border
              print:bg-white print:text-black"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(documentHtml) }}
          />
        </CardContent>
      </Card>

      {/* Footer info - Hidden on print */}
      <Card className="print:hidden">
        <CardContent className="py-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div>
              <p>Versão: v{etp.version}</p>
              <p>Criado em: {new Date(etp.created_at).toLocaleDateString('pt-BR')}</p>
            </div>
            <div className="text-right">
              {etp.numero_processo && (
                <p>Processo: {etp.numero_processo}</p>
              )}
              <p>Status: {etp.status}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
    </PermissionGuard>
  );
}
