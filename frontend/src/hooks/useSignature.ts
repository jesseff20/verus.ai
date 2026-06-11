import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import api from '@/lib/api';

export type SignatureProvider = {
  id: string;
  name: string;
  description: string;
  icon: string;
  available: boolean;
  requires_config: string[];
  validade_anos: number;
  aceito_juridicamente: boolean;
  observacao?: string;
  lei?: string;
};

export type DigitalSignatureDto = {
  id: string;
  signer: string;
  signer_name: string;
  document_type: string;
  document_ref: string;
  document_title: string;
  content_hash: string;
  provider: string;
  provider_label: string;
  status: 'pending' | 'signed' | 'rejected' | 'expired' | 'revoked';
  status_label: string;
  public_key_fingerprint: string;
  signed_at: string | null;
  expires_at: string | null;
  signer_ip: string | null;
  created_at: string;
};

export type SignDocumentPayload = {
  content: string;
  document_type: string;
  document_ref: string;
  document_title?: string;
  provider: string;
};

const BASE = '/api/v1/signatures';

export function useSignatureProviders() {
  return useQuery<SignatureProvider[]>({
    queryKey: ['signature-providers'],
    queryFn: async () => {
      const { data } = await api.get(`${BASE}/providers/`);
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useMySignatures() {
  return useQuery<DigitalSignatureDto[]>({
    queryKey: ['signatures', 'mine'],
    queryFn: async () => {
      const { data } = await api.get(`${BASE}/`);
      return data.results ?? data;
    },
    staleTime: 30_000,
  });
}

export function useDocumentSignatures(documentRef: string, documentType?: string) {
  return useQuery<DigitalSignatureDto[]>({
    queryKey: ['signatures', documentRef, documentType],
    queryFn: async () => {
      const params = new URLSearchParams({ document_ref: documentRef });
      if (documentType) params.set('document_type', documentType);
      const { data } = await api.get(`${BASE}/?${params}`);
      return data.results ?? data;
    },
    enabled: Boolean(documentRef),
  });
}

export function useSignDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SignDocumentPayload) => {
      const { data } = await api.post<DigitalSignatureDto>(`${BASE}/sign/`, payload);
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['signatures', data.document_ref] });
      toast.success('Documento assinado com sucesso.');
    },
  });
}

export function useVerifySignature() {
  return useMutation({
    mutationFn: async (signatureId: string) => {
      const { data } = await api.post<{ valid: boolean; reason: string; signature: DigitalSignatureDto }>(
        `${BASE}/verify/`,
        { signature_id: signatureId },
      );
      return data;
    },
    onSuccess: (data) => {
      if (data.valid) {
        toast.success('Assinatura válida.');
      } else {
        toast.error(`Assinatura inválida: ${data.reason}`);
      }
    },
  });
}
