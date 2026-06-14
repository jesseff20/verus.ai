import React, { memo } from 'react';
import { motion } from 'motion/react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Upload,
  File,
  Loader2,
  Check,
  AlertCircle,
  Trash2,
  ArrowRight,
  FileUp,
  Brain,
  FileText,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

interface UploadPhaseProps {
  sessionDetail: any;
  isUploadingDocuments: boolean;
  dragActive: boolean;
  onDrag: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDeleteDocument: (id: string) => void;
  onAdvance: () => void;
  formatFileSize: (bytes: number) => string;
}

function UploadPhaseComponent({
  sessionDetail,
  isUploadingDocuments,
  dragActive,
  onDrag,
  onDrop,
  onFileSelect,
  onDeleteDocument,
  onAdvance,
  formatFileSize,
}: UploadPhaseProps) {
  const documents = sessionDetail?.documents || [];
  const stats = sessionDetail?.embedding_stats;

  return (
    <motion.div
      key="upload"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Upload de Referências</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Envie documentos para servir de base para a geração do conteúdo.
          </p>
        </div>
        {/* Desktop: inline button; Mobile: fixed bottom bar */}
        <Button
          onClick={onAdvance}
          className="hidden sm:flex gap-2 rounded-xl px-6 py-3 font-semibold shadow-lg shadow-primary/20"
        >
          Continuar para Geração
          <ArrowRight size={18} />
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8 pb-16 sm:pb-0">
        {/* Left: Upload + Documents */}
        <div className="lg:col-span-2 space-y-4 sm:space-y-6">
          {/* Drop zone - tap-friendly on mobile */}
          <label
            htmlFor="file-upload-phase"
            className={cn(
              'relative border-2 border-dashed rounded-2xl sm:rounded-3xl p-6 sm:p-10 flex flex-col items-center justify-center gap-3 sm:gap-4 bg-white transition-all cursor-pointer min-h-[140px] sm:min-h-0',
              'active:scale-[0.98] touch-manipulation',
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-slate-300 hover:border-primary/50'
            )}
            onDragEnter={onDrag}
            onDragLeave={onDrag}
            onDragOver={onDrag}
            onDrop={onDrop}
          >
            {isUploadingDocuments ? (
              <div className="text-center space-y-3">
                <Loader2 className="h-10 w-10 sm:h-12 sm:w-12 mx-auto animate-spin text-primary" />
                <p className="font-semibold text-slate-700 text-sm sm:text-base">Processando documentos...</p>
                <p className="text-xs sm:text-sm text-slate-400">Extraindo texto e gerando embeddings</p>
              </div>
            ) : (
              <>
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
                  <FileUp size={24} className="sm:w-7 sm:h-7" />
                </div>
                <div className="text-center">
                  <p className="text-base sm:text-lg font-semibold text-slate-700">
                    <span className="hidden sm:inline">Arraste arquivos ou clique para selecionar</span>
                    <span className="sm:hidden">Toque para selecionar arquivos</span>
                  </p>
                  <p className="text-xs sm:text-sm text-slate-400 mt-1">PDF, DOCX, TXT, ODT (Max. 10MB)</p>
                </div>
                <input
                  type="file"
                  id="file-upload-phase"
                  multiple
                  accept=".pdf,.docx,.txt,.odt"
                  onChange={onFileSelect}
                  className="hidden"
                />
                <Button
                  asChild
                  variant="outline"
                  className="rounded-xl pointer-events-none"
                >
                  <span>
                    <Upload className="h-4 w-4 mr-2" />
                    Selecionar Arquivos
                  </span>
                </Button>
              </>
            )}
          </label>

          {/* Documents list - scrollable on mobile */}
          <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-bold text-slate-800 flex items-center gap-2 text-sm sm:text-base">
                <File size={18} className="text-primary" />
                Documentos Enviados
              </h3>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                {documents.length} Arquivo{documents.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="divide-y divide-slate-100 max-h-[50vh] sm:max-h-none overflow-y-auto overscroll-contain">
              {documents.length === 0 ? (
                <div className="p-8 sm:p-10 text-center text-slate-400 italic text-sm">
                  Nenhum documento enviado ainda.
                </div>
              ) : (
                documents.map((doc: any) => (
                  <div
                    key={doc.id}
                    className="p-3 sm:p-4 flex items-center justify-between hover:bg-slate-50 transition-colors active:bg-slate-50"
                  >
                    <div className="flex items-center gap-3 sm:gap-4 min-w-0 flex-1">
                      <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500 font-bold text-xs uppercase shrink-0">
                        {doc.file_type}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-slate-700 text-sm truncate">{doc.filename}</p>
                        <div className="flex items-center gap-2 sm:gap-3 text-xs text-slate-400 mt-0.5">
                          <span>{formatFileSize(doc.file_size)}</span>
                          <span>&bull;</span>
                          <span
                            className={cn(
                              'flex items-center gap-1',
                              doc.extraction_status === 'completed'
                                ? 'text-emerald-500'
                                : doc.extraction_status === 'failed'
                                  ? 'text-red-500'
                                  : 'text-primary'
                            )}
                          >
                            {doc.extraction_status === 'completed' && <CheckCircle2 size={12} />}
                            {doc.extraction_status === 'failed' && <XCircle size={12} />}
                            {doc.extraction_status !== 'completed' &&
                              doc.extraction_status !== 'failed' && (
                                <Loader2 size={12} className="animate-spin" />
                              )}
                            {doc.extraction_status === 'completed'
                              ? 'Pronto'
                              : doc.extraction_status === 'failed'
                                ? 'Falhou'
                                : 'Processando...'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => onDeleteDocument(doc.id)}
                      className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all active:bg-red-500/10 touch-manipulation shrink-0"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: Tips + Stats */}
        <div className="space-y-4 sm:space-y-6">
          {/* Embedding stats */}
          {stats && stats.documents_processed > 0 && (
            <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200 p-4 sm:p-6 shadow-sm">
              <h3 className="font-bold text-slate-800 text-sm mb-3">Estatísticas</h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center">
                  <p className="text-xl font-black text-primary">{stats.documents_processed}</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Docs</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-black text-slate-800">{stats.total_chunks}</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Chunks</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-black text-slate-800">
                    {(stats.total_characters / 1000).toFixed(1)}k
                  </p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase">Chars</p>
                </div>
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="bg-primary/5 border border-primary/10 rounded-2xl sm:rounded-3xl p-4 sm:p-6">
            <h3 className="font-bold text-primary flex items-center gap-2 mb-3 sm:mb-4 text-sm">
              <AlertCircle size={16} />
              Dicas de Upload
            </h3>
            <ul className="space-y-2 sm:space-y-3 text-sm text-slate-600">
              <li className="flex gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                Documentos de referência ajudam a IA a entender o tom e os requisitos técnicos.
              </li>
              <li className="flex gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                Envie editais anteriores, termos de referência ou manuais técnicos.
              </li>
              <li className="flex gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                O upload é opcional. A IA usará o objetivo e o blueprint se nenhum arquivo for enviado.
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Mobile: Fixed bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden z-40 bg-white/95 backdrop-blur-sm border-t border-slate-200 px-4 py-3 safe-area-bottom">
        <Button
          onClick={onAdvance}
          className="w-full gap-2 rounded-xl py-3 font-semibold shadow-lg shadow-primary/20 text-[16px]"
        >
          Continuar para Geração
          <ArrowRight size={18} />
        </Button>
      </div>
    </motion.div>
  );
}

export const UploadPhase = memo(UploadPhaseComponent);
