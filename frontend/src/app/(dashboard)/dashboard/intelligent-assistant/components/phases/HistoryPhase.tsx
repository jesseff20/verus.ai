import React, { memo } from 'react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Download,
  Eye,
  Trash2,
  History,
  Calendar,
  FileText,
} from 'lucide-react';

interface HistoryPhaseProps {
  sessionDetail: any;
  totalSections: number;
  onLoadDocument: (doc: any) => void;
  onDeleteDocument: (id: string) => void;
}

function HistoryPhaseComponent({
  sessionDetail,
  totalSections,
  onLoadDocument,
  onDeleteDocument,
}: HistoryPhaseProps) {
  const documents = sessionDetail?.generated_documents || [];

  return (
    <motion.div
      key="history"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Histórico da Sessão</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Versões geradas e salvas durante este projeto.
        </p>
      </div>

      {documents.length === 0 ? (
        <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm p-16 text-center">
          <History className="h-16 w-16 mx-auto mb-4 text-slate-300" />
          <h3 className="text-lg font-semibold text-slate-600 mb-2">Nenhum documento no histórico</h3>
          <p className="text-sm text-slate-400">Os documentos gerados aparecerão aqui.</p>
        </div>
      ) : (
        <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Documento
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Data / Hora
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Score Médio
                </th>
                <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Seções
                </th>
                <th className="px-6 py-4 text-right text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.map((doc: any) => {
                const avgScore = doc.metadata?.sections_stats?.average_score;
                const validCount = doc.metadata?.sections_stats?.valid_count;
                const docTotalSections = doc.metadata?.sections_stats?.total_sections || totalSections;

                return (
                  <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                          <FileText className="h-5 w-5 text-primary" />
                        </div>
                        <span className="font-bold text-slate-700 text-sm">
                          {doc.title || 'Documento Gerado'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-1.5 text-sm text-slate-600">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        {doc.created_at
                          ? new Date(doc.created_at).toLocaleString('pt-BR')
                          : '-'}
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      {avgScore !== undefined ? (
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'text-sm font-black',
                              avgScore >= 80 ? 'text-emerald-500' : avgScore >= 60 ? 'text-amber-500' : 'text-red-500'
                            )}
                          >
                            {Math.round(avgScore)}%
                          </span>
                          <div className="w-16 h-1 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                'h-full rounded-full',
                                avgScore >= 80 ? 'bg-emerald-500' : avgScore >= 60 ? 'bg-amber-500' : 'bg-red-500'
                              )}
                              style={{ width: `${avgScore}%` }}
                            />
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-400 text-sm">--</span>
                      )}
                    </td>
                    <td className="px-6 py-5">
                      <Badge variant="secondary" className="text-xs">
                        {validCount !== undefined ? `${validCount}/${docTotalSections}` : '--'} Seções
                      </Badge>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {doc.pdf_url && (
                          <Button variant="outline" size="sm" asChild className="rounded-lg">
                            <a href={doc.pdf_url} target="_blank" rel="noopener noreferrer">
                              <Download className="h-4 w-4 mr-1" />
                              PDF
                            </a>
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onLoadDocument(doc)}
                          className="rounded-lg text-primary font-bold"
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          Visualizar
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-400 hover:text-red-600 hover:bg-red-50"
                          onClick={() => onDeleteDocument(doc.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </motion.div>
  );
}

export const HistoryPhase = memo(HistoryPhaseComponent);
