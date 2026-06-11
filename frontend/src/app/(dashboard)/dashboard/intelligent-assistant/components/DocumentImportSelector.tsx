'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, FileText, Link2, CheckCircle2, AlertCircle, X } from 'lucide-react';
import api from '@/lib/api';

interface PreviousSession {
  id: string;
  objective: string;
  status: string;
  document_type: string;
  created_at: string;
  documents_count: number;
}

interface DocumentImportSelectorProps {
  targetDocumentType: string;
  sourceCodes: { code: string; label: string }[];
  onSelect: (sessionId: string | null) => void;
  onSkip: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  completed: 'Concluído',
  generating: 'Gerando',
  initialized: 'Iniciado',
  processing: 'Processando',
  failed: 'Falhou',
};

export function DocumentImportSelector({
  targetDocumentType,
  sourceCodes,
  onSelect,
  onSkip,
}: DocumentImportSelectorProps) {
  const [sessions, setSessions] = useState<{ type: string; label: string; items: PreviousSession[] }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      setIsLoading(true);
      try {
        const results = await Promise.all(
          sourceCodes.map(async ({ code, label }) => {
            const response = await api.get('/api/v1/intelligent-assistant/sessions/list/', {
              params: { document_type: code },
            });
            return {
              type: code,
              label,
              items: (response.data.sessions || []).filter((s: PreviousSession) => s.status === 'completed' || s.documents_count > 0),
            };
          })
        );
        setSessions(results.filter((r) => r.items.length > 0));
      } catch {
        setSessions([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSessions();
  }, [sourceCodes]);

  const allSessions = sessions.flatMap((g) => g.items.map((s) => ({ ...s, typeLabel: g.label })));

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-primary mr-2" />
          <span className="text-sm text-muted-foreground">Buscando documentos anteriores...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Link2 className="h-5 w-5 text-primary" />
          Vincular documento anterior
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Esta peça pode ser gerada com base em um documento anterior. Vincule ou pule para começar do zero.
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {allSessions.length === 0 ? (
          <div className="text-center py-6">
            <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">
              Nenhum {sourceCodes.map((s) => s.label).join(' ou ')} encontrado.
            </p>
            <Button variant="outline" onClick={onSkip} className="mt-4">
              Continuar sem vincular
            </Button>
          </div>
        ) : (
          <>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {allSessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => setSelectedId(session.id === selectedId ? null : session.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedId === session.id
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-border hover:border-primary/50 hover:bg-muted/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary shrink-0" />
                        <Badge variant="outline" className="text-[10px] shrink-0">
                          {(session as any).typeLabel}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {session.objective}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <Badge
                        variant={session.status === 'completed' ? 'default' : 'secondary'}
                        className="text-[10px]"
                      >
                        {STATUS_LABELS[session.status] || session.status}
                      </Badge>
                      <p className="text-[10px] text-muted-foreground mt-1">
                        {new Date(session.created_at).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {selectedId && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 border border-green-200">
                <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                <span className="text-sm text-green-800 flex-1">
                  Documento vinculado. A IA usará o contexto desta peça anterior.
                </span>
                <button onClick={() => setSelectedId(null)}>
                  <X className="h-4 w-4 text-green-600" />
                </button>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                onClick={() => onSelect(selectedId)}
                disabled={!selectedId}
                className="flex-1"
              >
                <Link2 className="h-4 w-4 mr-2" />
                {selectedId ? 'Vincular selecionado' : 'Selecione um documento'}
              </Button>
              <Button variant="outline" onClick={onSkip}>
                Pular
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
