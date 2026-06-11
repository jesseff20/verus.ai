'use client';

import { useAnalytics } from '@/hooks/use-analytics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, MessageSquare, FileText, ThumbsUp, TrendingUp, Clock, Coins } from 'lucide-react';
import { FeedbackTimelineChart } from '@/components/analytics/FeedbackTimelineChart';
import { TokensTimelineChart } from '@/components/analytics/TokensTimelineChart';
import { WordCloudChart } from '@/components/analytics/WordCloudChart';

export default function AnalyticsPage() {
  const {
    summary,
    feedbackTimeline,
    chartData,
    period,
    isSummaryLoading,
    wordCloudData,
    isWordCloudLoading
  } = useAnalytics();

  if (isSummaryLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics do Assistente</h1>
          <p className="text-muted-foreground">
            Nenhum dado de analytics disponível
          </p>
        </div>
      </div>
    );
  }

  const cards = [
    {
      title: 'Conversas',
      value: summary.total_conversations.toLocaleString('pt-BR'),
      description: `Últimos ${period?.days || 30} dias`,
      icon: MessageSquare,
      bgLight: 'bg-purple-50',
      iconColor: 'text-purple-600',
    },
    {
      title: 'Mensagens',
      value: summary.total_messages.toLocaleString('pt-BR'),
      description: `Últimos ${period?.days || 30} dias`,
      icon: FileText,
      bgLight: 'bg-pink-50',
      iconColor: 'text-pink-600',
    },
    {
      title: 'Feedbacks',
      value: summary.total_feedbacks.toLocaleString('pt-BR'),
      description: `${summary.positive_feedbacks} positivos, ${summary.negative_feedbacks} negativos`,
      icon: ThumbsUp,
      bgLight: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
    {
      title: 'Taxa de Satisfação',
      value: `${summary.avg_satisfaction.toFixed(1)}%`,
      description: 'Média dos últimos 30 dias',
      icon: TrendingUp,
      bgLight: 'bg-green-50',
      iconColor: 'text-green-600',
    },
    {
      title: 'Tempo Médio de Resposta',
      value: `${summary.avg_response_time}ms`,
      description: 'Performance das respostas',
      icon: Clock,
      bgLight: 'bg-orange-50',
      iconColor: 'text-orange-600',
    },
    {
      title: 'Tokens Utilizados',
      value: summary.total_tokens.toLocaleString('pt-BR'),
      description: 'Consumo total de tokens',
      icon: Coins,
      bgLight: 'bg-yellow-50',
      iconColor: 'text-yellow-600',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Analytics do Assistente</h1>
        <p className="text-muted-foreground">
          Métricas e estatísticas de uso dos últimos 30 dias
        </p>
      </div>

      {/* Cards de Métricas */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.title} className="hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {card.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${card.bgLight}`}>
                  <Icon className={`h-4 w-4 ${card.iconColor}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{card.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {card.description}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Gráfico de Série Temporal - Feedbacks */}
      {feedbackTimeline && feedbackTimeline.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Evolução de Feedbacks ao Longo do Tempo</CardTitle>
            <CardDescription>
              Feedbacks positivos e negativos dos últimos {period?.days || 30} dias
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FeedbackTimelineChart data={feedbackTimeline} />
          </CardContent>
        </Card>
      )}

      {/* Gráfico de Série Temporal - Tokens */}
      {chartData && chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Evolução do Uso de Tokens ao Longo do Tempo</CardTitle>
            <CardDescription>
              Total de tokens utilizados nos últimos {period?.days || 30} dias
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TokensTimelineChart data={chartData} />
          </CardContent>
        </Card>
      )}

      {/* Nuvens de Palavras */}
      {!isWordCloudLoading && wordCloudData && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Nuvem de Palavras - Entrada</CardTitle>
              <CardDescription>
                Palavras mais frequentes nas mensagens dos usuários
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WordCloudChart
                words={wordCloudData.input_words}
                title="Mensagens de Entrada (Usuários)"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Total de {wordCloudData.total_messages_analyzed.input} mensagens analisadas
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Nuvem de Palavras - Saída</CardTitle>
              <CardDescription>
                Palavras mais frequentes nas respostas do assistente
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WordCloudChart
                words={wordCloudData.output_words}
                title="Mensagens de Saída (Assistente)"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Total de {wordCloudData.total_messages_analyzed.output} mensagens analisadas
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {isWordCloudLoading && (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Carregando nuvens de palavras...
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    
  );
}
