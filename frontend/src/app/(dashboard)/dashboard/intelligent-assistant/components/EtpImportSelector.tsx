'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, FileText, ArrowRight, CheckCircle2, AlertCircle, Import } from 'lucide-react';
import api from '@/lib/api';

interface EtpSession {
  id: string;
  objective: string;
  status: string;
  blueprint_name: string;
  created_at: string;
  progress_percentage: number;
  completed_sections: number;
  total_sections: number;
}

interface ImportedSection {
  tr_section_number: number;
  tr_section_id: string;
  tr_section_name: string;
  import_type: string;
  etp_source_label: string;
  etp_sections_used: number[];
  imported_content: string;
  has_content: boolean;
  needs_ai: boolean;
  needs_input: boolean;
}

interface ImportStats {
  total_sections: number;
  imported_from_etp: number;
  needs_ai_generation: number;
  needs_manual_input: number;
  ready_to_use: number;
}

interface EtpImportSelectorProps {
  trBlueprintId: string;
  onImportComplete: (sections: ImportedSection[], etpSessionId: string) => void;
  onSkip: () => void;
}

export function EtpImportSelector({ trBlueprintId, onImportComplete, onSkip }: EtpImportSelectorProps) {
  const [etpSessions, setEtpSessions] = useState<EtpSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEtpId, setSelectedEtpId] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<{ sections: ImportedSection[]; stats: ImportStats } | null>(null);

  useEffect(() => {
    const fetchEtpSessions = async () => {
      try {
        const response = await api.get('/api/v1/intelligent-assistant/tr/etp-sessions/');
        setEtpSessions(response.data.etp_sessions || []);
      } catch {
        console.error('Erro ao buscar sessões do documento');
      } finally {
        setIsLoading(false);
      }
    };
    fetchEtpSessions();
  }, []);

  const handleImport = async () => {
    if (!selectedEtpId) return;
    setIsImporting(true);
    try {
      const response = await api.get(
        `/api/v1/intelligent-assistant/tr/import/${selectedEtpId}/`,
        { params: { tr_blueprint_id: trBlueprintId } }
      );
      setImportResult({
        sections: response.data.sections,
        stats: response.data.stats,
      });
    } catch {
      console.error('Erro ao importar documento');
    } finally {
      setIsImporting(false);
    }
  };

  const handleConfirm = () => {
    if (importResult && selectedEtpId) {
      onImportComplete(importResult.sections, selectedEtpId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-2 text-sm text-muted-foreground">Carregando documentos......</span>
      </div>
    );
  }

  // Se já importou, mostrar resumo
  if (importResult) {
    const { stats } = importResult;
    return (
      <Card className="border-green-200 bg-green-50/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            Documento importado com sucesso
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-600">{stats.imported_from_etp}</div>
              <div className="text-xs text-muted-foreground">Importadas do documento</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.needs_ai_generation}</div>
              <div className="text-xs text-muted-foreground">Precisam de IA</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-amber-600">{stats.needs_manual_input}</div>
              <div className="text-xs text-muted-foreground">Preenchimento manual</div>
            </div>
            <div className="bg-white rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-slate-600">{stats.ready_to_use}</div>
              <div className="text-xs text-muted-foreground">Prontas para uso</div>
            </div>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1">
            {importResult.sections.filter(s => s.has_content).map((sec) => (
              <div key={sec.tr_section_number} className="flex items-center gap-2 text-xs py-1 px-2 rounded bg-white">
                <Badge variant="outline" className="text-[10px] shrink-0">
                  §{sec.tr_section_number}
                </Badge>
                <span className="truncate">{sec.tr_section_name}</span>
                <Badge variant="secondary" className="text-[10px] ml-auto shrink-0">
                  {sec.etp_source_label}
                </Badge>
              </div>
            ))}
          </div>

          <Button onClick={handleConfirm} className="w-full">
            <ArrowRight className="h-4 w-4 mr-2" />
            Prosseguir com as seções importadas
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Import className="h-5 w-5 text-primary" />
          Importar dados do documento
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Esta peça pode reaproveitar dados de um documento já gerado. Selecione abaixo ou comece do zero.
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {etpSessions.length === 0 ? (
          <div className="text-center py-6">
            <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Nenhum documento encontrado.</p>
            <p className="text-xs text-muted-foreground mt-1">Gere um documento primeiro para poder importar dados.</p>
            <Button variant="outline" onClick={onSkip} className="mt-4">
              Continuar sem importar
            </Button>
          </div>
        ) : (
          <>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {etpSessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => setSelectedEtpId(session.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedEtpId === session.id
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-border hover:border-primary/50 hover:bg-muted/30'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary shrink-0" />
                        <span className="text-sm font-medium truncate">{session.blueprint_name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {session.objective}
                      </p>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <Badge variant={session.status === 'completed' ? 'default' : 'secondary'} className="text-[10px]">
                        {session.status === 'completed' ? 'Concluído' : session.status}
                      </Badge>
                      <p className="text-[10px] text-muted-foreground mt-1">
                        {session.completed_sections}/{session.total_sections} seções
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {new Date(session.created_at).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleImport}
                disabled={!selectedEtpId || isImporting}
                className="flex-1"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Importando...
                  </>
                ) : (
                  <>
                    <Import className="h-4 w-4 mr-2" />
                    Importar do documento selecionado
                  </>
                )}
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
