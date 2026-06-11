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
          ? 'border-white/10 hover:border-white/20 hover:bg-white/5'
          : 'border-white/5 opacity-40 cursor-not-allowed'
      }`}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl mt-0.5">{PROVIDER_ICONS[provider.id] || '📝'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white/80">{provider.name}</span>
            {provider.aceito_juridicamente && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                style={{ background: '#22C55E15', color: '#22C55E', border: '1px solid #22C55E30' }}
              >
                juridicamente válido
              </span>
            )}
            {!provider.available && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded font-mono"
                style={{ background: '#F59E0B15', color: '#F59E0B', border: '1px solid #F59E0B30' }}
              >
                não configurado
              </span>
            )}
          </div>
          <p className="text-[11px] text-white/40 mt-0.5 leading-relaxed">
            {provider.description}
          </p>
          {provider.lei && (
            <p className="text-[10px] text-white/25 mt-1">{provider.lei}</p>
          )}
          {provider.observacao && (
            <p className="text-[10px] text-amber-400/70 mt-1 flex items-center gap-1">
              <Info size={9} />
              {provider.observacao}
            </p>
          )}
        </div>
        {selected && (
          <CheckCircle2 size={14} style={{ color: '#7030A0', flexShrink: 0, marginTop: 2 }} />
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
      style={{ background: 'rgba(0,0,0,0.8)' }}
      onClick={onClose}
    >
      <div
        className="rounded-2xl border w-full max-w-lg mx-4 overflow-hidden"
        style={{ background: '#0D0D0D', borderColor: '#2A2A2A' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b" style={{ borderColor: '#1A1A1A' }}>
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: '#7030A015', border: '1px solid #7030A030' }}
          >
            <Shield size={15} className="text-[#8B5CF6]" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Assinar Documento</h2>
            <p className="text-[11px] text-white/40">{documentTitle || documentRef}</p>
          </div>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <div>
            <p className="text-xs font-mono uppercase tracking-widest text-white/30 mb-3">
              Escolha o método de assinatura
            </p>

            {loadingProviders ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="animate-spin text-white/20" />
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
          <div
            className="rounded-lg px-3 py-2 text-[10px] text-white/25 font-mono"
            style={{ background: '#ffffff06' }}
          >
            Conteúdo a assinar: {content.slice(0, 60)}{content.length > 60 ? '...' : ''}
          </div>
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-2 px-5 py-3 border-t"
          style={{ borderColor: '#1A1A1A', background: '#0A0A0A' }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/8 transition-all"
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
