'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import type { DocumentBlueprint, BlueprintSection } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Play, Loader2, Clock, Hash, CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import DOMPurify from 'isomorphic-dompurify';
import { AIEnhanceButton } from '@/components/ui/ai-enhance-button';
import { useToast } from '@/hooks/use-toast';

interface TestStepProps {
  blueprint: DocumentBlueprint;
}

interface TestResult {
  content: string;
  execution_time_ms?: number;
  tokens_used?: number;
  is_valid?: boolean;
}

/**
 * Step de teste de geração de seções individuais do blueprint.
 * Permite selecionar uma seção, definir um objetivo e testar a geração via IA.
 * Exibe o conteúdo gerado com métricas de performance.
 */
export function TestStep({ blueprint }: TestStepProps) {
  const { toast } = useToast();
  const sections = blueprint.sections || [];

  // Estado do formulário de teste
  const [selectedSectionId, setSelectedSectionId] = useState<string>('');
  const [objective, setObjective] = useState<string>('');
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  // Seção selecionada
  const selectedSection = sections.find((s) => s.id === selectedSectionId);

  // Mutation para executar o teste de geração
  const testMutation = useMutation({
    mutationFn: async ({ agentId, payload }: { agentId: string; payload: Record<string, any> }) => {
      const startTime = Date.now();
      const response = await api.post(
        `/api/v1/intelligent-assistant/agents/${agentId}/execute/`,
        payload,
        { timeout: 120000 } // 2 minutos de timeout para geração
      );
      const executionTime = Date.now() - startTime;
      return {
        ...response.data,
        execution_time_ms: response.data.execution_time_ms || executionTime,
      };
    },
    onSuccess: (data) => {
      setTestResult({
        content: data.response || data.content || data.generated_content || '',
        execution_time_ms: data.execution_time_ms,
        tokens_used: data.tokens_used || data.total_tokens,
        is_valid: data.is_valid,
      });
      toast({
        title: 'Geração concluída',
        description: 'A seção foi gerada com sucesso.',
      });
    },
    onError: (error: any) => {
      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        'Erro ao executar a geração. Verifique se o agente está configurado corretamente.';
      toast({
        title: 'Erro na geração',
        description: errorMessage,
        variant: 'destructive',
      });
    },
  });

  // Handler para executar o teste
  const handleTest = () => {
    if (!selectedSection) {
      toast({
        title: 'Selecione uma seção',
        description: 'Escolha uma seção do blueprint para testar.',
        variant: 'destructive',
      });
      return;
    }

    if (!objective.trim()) {
      toast({
        title: 'Informe o objetivo',
        description: 'Descreva o objetivo para a geração do conteúdo.',
        variant: 'destructive',
      });
      return;
    }

    const agentId = selectedSection.generator_agent_id;
    if (!agentId) {
      toast({
        title: 'Agente não configurado',
        description: `A seção "${selectedSection.section_name}" não possui um agente gerador vinculado.`,
        variant: 'destructive',
      });
      return;
    }

    // Limpar resultado anterior
    setTestResult(null);

    testMutation.mutate({
      agentId,
      payload: {
        objective: objective.trim(),
        section_name: selectedSection.section_name,
        section_number: selectedSection.section_number,
      },
    });
  };

  // Formatar tempo de execução
  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold">Testar Geração</h3>
        <p className="text-sm text-muted-foreground">
          Teste a geração de conteúdo de seções individuais do blueprint
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lado esquerdo: Configuração do teste */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Configuração do Teste</CardTitle>
              <CardDescription className="text-xs">
                Selecione a seção e defina o objetivo para gerar o conteúdo
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Selecionar seção */}
              <div className="space-y-2">
                <Label htmlFor="section-select">Seção</Label>
                {sections.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Este blueprint não possui seções configuradas.
                  </p>
                ) : (
                  <Select
                    value={selectedSectionId}
                    onValueChange={setSelectedSectionId}
                  >
                    <SelectTrigger id="section-select">
                      <SelectValue placeholder="Selecione uma seção..." />
                    </SelectTrigger>
                    <SelectContent>
                      {sections.map((section) => (
                        <SelectItem key={section.id} value={section.id}>
                          <span className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground font-mono">
                              {section.section_number}.
                            </span>
                            {section.section_name}
                            {!section.generator_agent_id && (
                              <Badge variant="outline" className="text-[10px] ml-1 text-amber-600 border-amber-300">
                                Sem agente
                              </Badge>
                            )}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              {/* Info da seção selecionada */}
              {selectedSection && (
                <div className="rounded-lg bg-muted/50 p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground">
                      Seção {selectedSection.section_number}
                    </span>
                    {selectedSection.is_required && (
                      <Badge variant="outline" className="text-[10px] bg-red-50 text-red-600 border-red-200">
                        Obrigatória
                      </Badge>
                    )}
                  </div>
                  {selectedSection.description && (
                    <p className="text-xs text-muted-foreground">
                      {selectedSection.description}
                    </p>
                  )}
                  {selectedSection.generator_agent_id ? (
                    <div className="flex items-center gap-1.5 text-[10px] text-primary">
                      <Sparkles size={10} />
                      <span>Agente: {selectedSection.generator_agent_name}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-[10px] text-amber-600">
                      <AlertCircle size={10} />
                      <span>Nenhum agente gerador vinculado</span>
                    </div>
                  )}
                </div>
              )}

              {/* Objetivo */}
              <div className="space-y-2">
                <Label htmlFor="objective">Objetivo</Label>
                <div className="relative">
                  <Textarea
                    id="objective"
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                    placeholder="Descreva o objetivo para a geração desta seção. Ex: Elaborar uma petição inicial de indenização por danos morais e materiais..."
                    rows={5}
                    className="resize-none pr-32"
                  />
                  <div className="absolute top-1 right-1">
                    <AIEnhanceButton
                      value={objective}
                      onEnhance={setObjective}
                      context="objetivo de geração de seção de documento jurídico"
                    />
                  </div>
                </div>
                <p className="text-[10px] text-muted-foreground">
                  O objetivo será enviado como contexto para o agente gerador da seção.
                </p>
              </div>

              {/* Botão de teste */}
              <Button
                onClick={handleTest}
                disabled={testMutation.isPending || !selectedSectionId || !objective.trim()}
                className="w-full"
                size="lg"
              >
                {testMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Gerando conteúdo...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Testar Geração
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Lado direito: Resultado */}
        <div className="space-y-4">
          <Card className="h-full">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold">Resultado</CardTitle>
                {testResult && (
                  <div className="flex items-center gap-2">
                    {testResult.is_valid !== undefined && (
                      <Badge
                        variant={testResult.is_valid ? 'default' : 'destructive'}
                        className="text-[10px]"
                      >
                        {testResult.is_valid ? 'Válido' : 'Inválido'}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
              <CardDescription className="text-xs">
                Conteúdo gerado pelo agente e métricas de execução
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Estado de carregamento */}
              {testMutation.isPending && (
                <div className="flex flex-col items-center justify-center py-16">
                  <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                  <p className="text-sm text-muted-foreground">Gerando conteúdo...</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Isso pode levar alguns segundos
                  </p>
                </div>
              )}

              {/* Estado vazio */}
              {!testMutation.isPending && !testResult && (
                <div className="flex flex-col items-center justify-center py-16">
                  <Play className="h-10 w-10 text-muted-foreground/30 mb-4" />
                  <p className="text-sm text-muted-foreground">
                    Nenhum teste executado
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Selecione uma seção e clique em &quot;Testar Geração&quot;
                  </p>
                </div>
              )}

              {/* Resultado da geração */}
              {!testMutation.isPending && testResult && (
                <div className="space-y-4">
                  {/* Métricas */}
                  <div className="grid grid-cols-3 gap-3">
                    {testResult.execution_time_ms !== undefined && (
                      <div className="rounded-lg bg-muted/50 p-2 text-center">
                        <div className="flex items-center justify-center gap-1 mb-1">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                        </div>
                        <p className="text-sm font-bold text-primary">
                          {formatTime(testResult.execution_time_ms)}
                        </p>
                        <p className="text-[10px] text-muted-foreground">Tempo</p>
                      </div>
                    )}
                    {testResult.tokens_used !== undefined && (
                      <div className="rounded-lg bg-muted/50 p-2 text-center">
                        <div className="flex items-center justify-center gap-1 mb-1">
                          <Hash className="h-3 w-3 text-muted-foreground" />
                        </div>
                        <p className="text-sm font-bold text-primary">
                          {testResult.tokens_used.toLocaleString('pt-BR')}
                        </p>
                        <p className="text-[10px] text-muted-foreground">Tokens</p>
                      </div>
                    )}
                    {testResult.is_valid !== undefined && (
                      <div className="rounded-lg bg-muted/50 p-2 text-center">
                        <div className="flex items-center justify-center gap-1 mb-1">
                          <CheckCircle className="h-3 w-3 text-muted-foreground" />
                        </div>
                        <p className="text-sm font-bold text-primary">
                          {testResult.is_valid ? 'Aprovado' : 'Reprovado'}
                        </p>
                        <p className="text-[10px] text-muted-foreground">Validação</p>
                      </div>
                    )}
                  </div>

                  <Separator />

                  {/* Conteúdo gerado */}
                  <ScrollArea className="h-[400px] w-full rounded-lg border p-4">
                    <div className="prose prose-sm max-w-none">
                      <div
                        className="text-sm leading-relaxed whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(testResult.content
                            .replace(/\n/g, '<br />')
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*(.*?)\*/g, '<em>$1</em>')),
                        }}
                      />
                    </div>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default TestStep;
