'use client';

import { useState } from 'react';
import {
  Shield, ShieldCheck, AlertCircle, Loader2,
  ChevronRight, CheckCircle2, XCircle, Info,
} from 'lucide-react';
import {
  useSignatureProviders,
  useSignDocument,
  useDocumentSignatures,
  type SignatureProvider,
  type SignDocumentPayload,
} from '@/hooks/useSignature';

const PROVIDER_ICONS: Record<string, string> = {
  internal: '🔐',
  govbr: '🇧🇷',
  icpbrasil: '📜',
  docusign: '✍️',
  certisign: '🏛️',
  serpro: '⚙️',
};

function ProviderCard({
  provider,
  selected,
  onSelect,
}: {
  provider: SignatureProvider;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      disabled={!provider.available}
      className={`w-full text-left p-3 rounded-xl border transition-all ${
        selected
          ? 'border-[#7030A0] bg-[#7030A015]'
          : provider.available
          ? 'border-border hover:border-muted-foreground/30 hover:bg-muted/50'
          : 'border-border/50 opacity-40 cursor-not-allowed'
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl mt-0.5">{PROVIDER_ICONS[provider.id] || '📝'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground/80">{provider.name}</span>
            {provider.aceito_juridicamente && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/20"
              >
                juridicamente válido
              </span>
            )}
            {!provider.available && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
              >
                não configurado
              </span>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
            {provider.description}
          </p>
          {provider.lei && (
            <p className="text-[10px] text-muted-foreground/60 mt-1">{provider.lei}</p>
          )}
          {provider.observacao && (
            <p className="text-[10px] text-amber-600 dark:text-amber-400/70 mt-1 flex items-center gap-1">
              <Info size={9} />
              {provider.observacao}
            </p>
          )}
        </div>
        {selected && (
          <CheckCircle2 size={14} className="text-[#7030A0] shrink-0 mt-0.5" />
        )}
      </div>
    </button>
  );
}

export function SignatureModal({
  documentRef,
  documentType,
  documentTitle,
  content,
  onClose,
  onSigned,
}: {
  documentRef: string;
  documentType: string;
  documentTitle?: string;
  content: string;
  onClose: () => void;
  onSigned?: (signatureId: string) => void;
}) {
  const [selectedProvider, setSelectedProvider] = useState('internal');
  const { data: providers = [], isLoading: loadingProviders } = useSignatureProviders();
  const signDoc = useSignDocument();

  const handleSign = async () => {
    const payload: SignDocumentPayload = {
      content,
      document_type: documentType,
      document_ref: documentRef,
      document_title: documentTitle || '',
      provider: selectedProvider,
    };

    const result = await signDoc.mutateAsync(payload).catch(() => null);
    if (result) {
      onSigned?.(result.id);
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.6)' }}
      onClick={onClose}
    >
      <div
        className="rounded-2xl border border-border bg-card w-full max-w-lg mx-4 overflow-hidden shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-border">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-primary/10 border border-primary/20">
            <Shield size={15} className="text-primary" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Assinar Documento</h2>
            <p className="text-[11px] text-muted-foreground">{documentTitle || documentRef}</p>
          </div>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <div>
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground/60 mb-3">
              Escolha o método de assinatura
            </p>

            {loadingProviders ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="animate-spin text-muted-foreground/40" />
              </div>
            ) : (
              <div className="space-y-2">
                {providers.map((p) => (
                  <ProviderCard
                    key={p.id}
                    provider={p}
                    selected={selectedProvider === p.id}
                    onSelect={() => p.available && setSelectedProvider(p.id)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Hash preview */}
          <div className="rounded-lg px-3 py-2 text-[10px] text-muted-foreground/60 font-mono bg-muted/50">
            Conteúdo a assinar: {content.slice(0, 60)}{content.length > 60 ? '...' : ''}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-border bg-muted/30">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-all"
          >
            Cancelar
          </button>
          <button
            onClick={handleSign}
            disabled={signDoc.isPending || !selectedProvider}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: '#7030A0', color: '#fff' }}
          >
            {signDoc.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <ShieldCheck size={14} />
            )}
            Assinar
          </button>
        </div>
      </div>
    </div>
  );
}
