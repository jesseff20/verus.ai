'use client';

import { ShieldCheck, ShieldAlert, Shield } from 'lucide-react';
import { useDocumentSignatures } from '@/hooks/useSignature';

export function SignatureBadge({
  documentRef,
  documentType,
}: {
  documentRef: string;
  documentType?: string;
}) {
  const { data: sigs = [], isLoading } = useDocumentSignatures(documentRef, documentType);

  if (isLoading) return null;

  const signed = sigs.filter((s) => s.status === 'signed');
  if (signed.length === 0) return null;

  const hasJuridical = signed.some(
    (s) => s.provider !== 'internal'
  );

  return (
    <div className="flex items-center gap-1.5">
      {hasJuridical ? (
        <ShieldCheck size={13} style={{ color: '#22C55E' }} />
      ) : (
        <Shield size={13} style={{ color: '#8B5CF6' }} />
      )}
      <span className="text-[11px]" style={{ color: hasJuridical ? '#22C55E' : '#8B5CF6' }}>
        {signed.length} assinatura{signed.length !== 1 ? 's' : ''}
        {hasJuridical ? ' (c/ validade jurídica)' : ' (interna)'}
      </span>
    </div>
  );
}
