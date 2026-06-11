'use client';

import { useState, useMemo } from 'react';
import DOMPurify from 'isomorphic-dompurify';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AIInput } from '@/components/ui/ai-input';
import { AITextarea } from '@/components/ui/ai-textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Mail,
  Plus,
  Eye,
  Pencil,
  Trash2,
  Sparkles,
  Loader2,
  X,
  Copy,
  Search,
  FileText,
  Clock,
  Gavel,
  FileCheck,
  Receipt,
  UserPlus,
  Code,
  LayoutTemplate,
  ChevronRight,
} from 'lucide-react';
import {
  useEmailTemplates,
  useCreateEmailTemplate,
  useUpdateEmailTemplate,
  useDeleteEmailTemplate,
  usePreviewEmailTemplate,
  useGenerateEmailTemplateAI,
  type EmailTemplate,
  type TemplateVariable,
} from '@/hooks/use-email-templates';

// ── Category Config ──

const categoryConfig: Record<string, { label: string; className: string; icon: React.ReactNode }> = {
  welcome: { label: 'Boas-vindas', className: 'bg-emerald-100 text-emerald-800 border-emerald-200', icon: <UserPlus className="h-3.5 w-3.5" /> },
  deadline_reminder: { label: 'Lembrete de Prazo', className: 'bg-red-100 text-red-700 border-red-200', icon: <Clock className="h-3.5 w-3.5" /> },
  hearing_notice: { label: 'Audiência', className: 'bg-purple-100 text-purple-800 border-purple-200', icon: <Gavel className="h-3.5 w-3.5" /> },
  document_ready: { label: 'Documento Pronto', className: 'bg-blue-100 text-blue-800 border-blue-200', icon: <FileCheck className="h-3.5 w-3.5" /> },
  invoice: { label: 'Fatura', className: 'bg-amber-100 text-amber-800 border-amber-200', icon: <Receipt className="h-3.5 w-3.5" /> },
  follow_up: { label: 'Follow-up', className: 'bg-cyan-100 text-cyan-800 border-cyan-200', icon: <Mail className="h-3.5 w-3.5" /> },
  notification: { label: 'Notificação', className: 'bg-blue-100 text-blue-800 border-blue-200', icon: <Mail className="h-3.5 w-3.5" /> },
  deadline: { label: 'Prazo', className: 'bg-red-100 text-red-700 border-red-200', icon: <Clock className="h-3.5 w-3.5" /> },
  client: { label: 'Cliente', className: 'bg-green-100 text-green-800 border-green-200', icon: <UserPlus className="h-3.5 w-3.5" /> },
  billing: { label: 'Cobrança', className: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: <Receipt className="h-3.5 w-3.5" /> },
  general: { label: 'Geral', className: 'bg-gray-100 text-gray-700 border-gray-200', icon: <FileText className="h-3.5 w-3.5" /> },
};

// ── Available Variables ──

const availableVariables = [
  { name: 'client_name', description: 'Nome completo do cliente' },
  { name: 'case_number', description: 'Número do processo' },
  { name: 'lawyer_name', description: 'Nome do advogado responsável' },
  { name: 'office_name', description: 'Nome do escritório' },
  { name: 'deadline_date', description: 'Data do prazo' },
  { name: 'hearing_date', description: 'Data da audiência' },
  { name: 'hearing_location', description: 'Local da audiência' },
  { name: 'document_name', description: 'Nome do documento' },
  { name: 'invoice_number', description: 'Número da fatura' },
  { name: 'invoice_amount', description: 'Valor da fatura' },
  { name: 'due_date', description: 'Data de vencimento' },
  { name: 'office_phone', description: 'Telefone do escritório' },
  { name: 'office_email', description: 'E-mail do escritório' },
  { name: 'office_address', description: 'Endereço do escritório' },
];

// ── Sample Data for Preview ──

const sampleData: Record<string, string> = {
  client_name: 'Maria Silva',
  case_number: '0001234-56.2024.8.26.0100',
  lawyer_name: 'Dr. João Santos',
  office_name: 'Santos & Associados Advocacia',
  deadline_date: '15/01/2025',
  hearing_date: '20/02/2025 as 14:00',
  hearing_location: '3a Vara Civel do Foro Central - São Paulo/SP',
  document_name: 'Procuração Ad Judicia',
  invoice_number: 'FAT-2025-0042',
  invoice_amount: 'R$ 3.500,00',
  due_date: '10/02/2025',
  office_phone: '(11) 3456-7890',
  office_email: 'contato@santosadvocacia.com.br',
  office_address: 'Av. Paulista, 1000, Sala 501 - São Paulo/SP',
};

// ── Pre-built Templates ──

interface PrebuiltTemplate {
  name: string;
  subject: string;
  category: string;
  body_html: string;
  variables: TemplateVariable[];
}

const prebuiltTemplates: PrebuiltTemplate[] = [
  {
    name: 'Boas-vindas ao Cliente',
    subject: 'Bem-vindo(a) ao {{office_name}}, {{client_name}}!',
    category: 'welcome',
    variables: [
      { name: 'client_name', description: 'Nome do cliente' },
      { name: 'lawyer_name', description: 'Nome do advogado' },
      { name: 'office_name', description: 'Nome do escritório' },
      { name: 'case_number', description: 'Número do processo' },
      { name: 'office_phone', description: 'Telefone do escritório' },
      { name: 'office_email', description: 'E-mail do escritório' },
    ],
    body_html: `<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%); padding: 32px 24px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{{office_name}}</h1>
    <p style="color: #a3c4e8; margin: 8px 0 0; font-size: 14px;">Advocacia &amp; Consultoria Jurídica</p>
  </div>
  <div style="background: #ffffff; padding: 32px 24px; border: 1px solid #e5e7eb; border-top: none;">
    <h2 style="color: #1e3a5f; margin: 0 0 16px; font-size: 20px;">Bem-vindo(a), {{client_name}}!</h2>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">E com grande satisfação que damos as boas-vindas ao nosso escritório. Agradecemos a confiança depositada em nossa equipe.</p>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Seu caso foi registrado com sucesso em nosso sistema:</p>
    <div style="background: #f3f4f6; border-left: 4px solid #2d5a8e; padding: 16px; margin: 16px 0; border-radius: 0 4px 4px 0;">
      <p style="margin: 0 0 8px; color: #6b7280; font-size: 13px;">NÚMERO DO PROCESSO</p>
      <p style="margin: 0; color: #1e3a5f; font-size: 16px; font-weight: 600;">{{case_number}}</p>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">O advogado responsável pelo seu caso e <strong>{{lawyer_name}}</strong>, que estara a disposição para esclarecer quaisquer dúvidas.</p>
    <div style="background: #eff6ff; border-radius: 8px; padding: 20px; margin: 24px 0;">
      <h3 style="color: #1e3a5f; margin: 0 0 12px; font-size: 15px;">Próximos passos:</h3>
      <ul style="color: #374151; line-height: 1.8; margin: 0; padding-left: 20px;">
        <li>Enviar os documentos solicitados</li>
        <li>Agendar reunião inicial com seu advogado</li>
        <li>Acessar o portal do cliente para acompanhar o andamento</li>
      </ul>
    </div>
    <div style="text-align: center; margin: 24px 0;">
      <a href="#" style="background: #2d5a8e; color: #ffffff; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block;">Acessar Portal do Cliente</a>
    </div>
  </div>
  <div style="background: #f9fafb; padding: 24px; text-align: center; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="color: #6b7280; font-size: 13px; margin: 0 0 4px;">{{office_name}}</p>
    <p style="color: #9ca3af; font-size: 12px; margin: 0 0 4px;">Tel: {{office_phone}} | E-mail: {{office_email}}</p>
    <p style="color: #9ca3af; font-size: 11px; margin: 12px 0 0;"><a href="#" style="color: #9ca3af;">Cancelar inscrição</a></p>
  </div>
</div>`,
  },
  {
    name: 'Lembrete de Prazo',
    subject: 'URGENTE: Prazo em {{deadline_date}} - Processo {{case_number}}',
    category: 'deadline_reminder',
    variables: [
      { name: 'client_name', description: 'Nome do cliente' },
      { name: 'case_number', description: 'Número do processo' },
      { name: 'deadline_date', description: 'Data do prazo' },
      { name: 'lawyer_name', description: 'Nome do advogado' },
      { name: 'office_name', description: 'Nome do escritório' },
      { name: 'office_phone', description: 'Telefone do escritório' },
      { name: 'office_email', description: 'E-mail do escritório' },
    ],
    body_html: `<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%); padding: 32px 24px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{{office_name}}</h1>
    <p style="color: #a3c4e8; margin: 8px 0 0; font-size: 14px;">Advocacia &amp; Consultoria Jurídica</p>
  </div>
  <div style="background: #ffffff; padding: 32px 24px; border: 1px solid #e5e7eb; border-top: none;">
    <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin: 0 0 24px; text-align: center;">
      <p style="color: #dc2626; font-weight: 700; font-size: 14px; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 1px;">Lembrete de Prazo Processual</p>
      <p style="color: #991b1b; font-size: 22px; font-weight: 700; margin: 0;">{{deadline_date}}</p>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Prezado(a) <strong>{{client_name}}</strong>,</p>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Gostaríamos de lembrar que existe um <strong>prazo processual importante</strong> se aproximando referente ao seu caso:</p>
    <div style="background: #f3f4f6; border-left: 4px solid #dc2626; padding: 16px; margin: 16px 0; border-radius: 0 4px 4px 0;">
      <p style="margin: 0 0 8px; color: #6b7280; font-size: 13px;">PROCESSO</p>
      <p style="margin: 0 0 12px; color: #1e3a5f; font-size: 16px; font-weight: 600;">{{case_number}}</p>
      <p style="margin: 0 0 8px; color: #6b7280; font-size: 13px;">DATA LIMITE</p>
      <p style="margin: 0; color: #dc2626; font-size: 16px; font-weight: 600;">{{deadline_date}}</p>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 16px 0;">Caso precise enviar algum documento ou tenha dúvidas, entre em contato com <strong>{{lawyer_name}}</strong> o mais breve possível.</p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="#" style="background: #dc2626; color: #ffffff; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block;">Ver Detalhes do Prazo</a>
    </div>
  </div>
  <div style="background: #f9fafb; padding: 24px; text-align: center; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="color: #6b7280; font-size: 13px; margin: 0 0 4px;">{{office_name}}</p>
    <p style="color: #9ca3af; font-size: 12px; margin: 0 0 4px;">Tel: {{office_phone}} | E-mail: {{office_email}}</p>
    <p style="color: #9ca3af; font-size: 11px; margin: 12px 0 0;"><a href="#" style="color: #9ca3af;">Cancelar inscrição</a></p>
  </div>
</div>`,
  },
  {
    name: 'Audiência Agendada',
    subject: 'Audiência Agendada - {{hearing_date}} - Processo {{case_number}}',
    category: 'hearing_notice',
    variables: [
      { name: 'client_name', description: 'Nome do cliente' },
      { name: 'case_number', description: 'Número do processo' },
      { name: 'hearing_date', description: 'Data e hora da audiência' },
      { name: 'hearing_location', description: 'Local da audiência' },
      { name: 'lawyer_name', description: 'Nome do advogado' },
      { name: 'office_name', description: 'Nome do escritório' },
      { name: 'office_phone', description: 'Telefone do escritório' },
      { name: 'office_email', description: 'E-mail do escritório' },
    ],
    body_html: `<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%); padding: 32px 24px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{{office_name}}</h1>
    <p style="color: #a3c4e8; margin: 8px 0 0; font-size: 14px;">Advocacia &amp; Consultoria Jurídica</p>
  </div>
  <div style="background: #ffffff; padding: 32px 24px; border: 1px solid #e5e7eb; border-top: none;">
    <div style="background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 8px; padding: 16px; margin: 0 0 24px; text-align: center;">
      <p style="color: #7c3aed; font-weight: 700; font-size: 14px; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 1px;">Audiência Agendada</p>
      <p style="color: #5b21b6; font-size: 20px; font-weight: 700; margin: 0;">{{hearing_date}}</p>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Prezado(a) <strong>{{client_name}}</strong>,</p>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Informamos que foi designada uma <strong>audiência</strong> no seu processo. Seguem os detalhes:</p>
    <div style="background: #f3f4f6; border-radius: 8px; padding: 20px; margin: 16px 0;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px; width: 120px; vertical-align: top;">PROCESSO</td>
          <td style="padding: 8px 0; color: #1e3a5f; font-weight: 600;">{{case_number}}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">DATA/HORA</td>
          <td style="padding: 8px 0; color: #1e3a5f; font-weight: 600;">{{hearing_date}}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">LOCAL</td>
          <td style="padding: 8px 0; color: #1e3a5f; font-weight: 600;">{{hearing_location}}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280; font-size: 13px; vertical-align: top;">ADVOGADO</td>
          <td style="padding: 8px 0; color: #1e3a5f; font-weight: 600;">{{lawyer_name}}</td>
        </tr>
      </table>
    </div>
    <div style="background: #eff6ff; border-radius: 8px; padding: 20px; margin: 24px 0;">
      <h3 style="color: #1e3a5f; margin: 0 0 12px; font-size: 15px;">Orientações importantes:</h3>
      <ul style="color: #374151; line-height: 1.8; margin: 0; padding-left: 20px;">
        <li>Comparecer com <strong>15 minutos de antecedência</strong></li>
        <li>Levar documento de identidade com foto (RG ou CNH)</li>
        <li>Trazer todos os documentos originais solicitados</li>
        <li>Vestir-se de forma adequada</li>
      </ul>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 16px 0;">Em caso de impossibilidade de comparecimento, entre em contato <strong>imediatamente</strong> com o escritório.</p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="#" style="background: #7c3aed; color: #ffffff; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block;">Confirmar Presença</a>
    </div>
  </div>
  <div style="background: #f9fafb; padding: 24px; text-align: center; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="color: #6b7280; font-size: 13px; margin: 0 0 4px;">{{office_name}}</p>
    <p style="color: #9ca3af; font-size: 12px; margin: 0 0 4px;">Tel: {{office_phone}} | E-mail: {{office_email}}</p>
    <p style="color: #9ca3af; font-size: 11px; margin: 12px 0 0;"><a href="#" style="color: #9ca3af;">Cancelar inscrição</a></p>
  </div>
</div>`,
  },
  {
    name: 'Documento Pronto',
    subject: 'Documento Disponível: {{document_name}} - Processo {{case_number}}',
    category: 'document_ready',
    variables: [
      { name: 'client_name', description: 'Nome do cliente' },
      { name: 'case_number', description: 'Número do processo' },
      { name: 'document_name', description: 'Nome do documento' },
      { name: 'lawyer_name', description: 'Nome do advogado' },
      { name: 'office_name', description: 'Nome do escritório' },
      { name: 'office_phone', description: 'Telefone do escritório' },
      { name: 'office_email', description: 'E-mail do escritório' },
    ],
    body_html: `<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%); padding: 32px 24px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{{office_name}}</h1>
    <p style="color: #a3c4e8; margin: 8px 0 0; font-size: 14px;">Advocacia &amp; Consultoria Jurídica</p>
  </div>
  <div style="background: #ffffff; padding: 32px 24px; border: 1px solid #e5e7eb; border-top: none;">
    <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 16px; margin: 0 0 24px; text-align: center;">
      <p style="color: #059669; font-weight: 700; font-size: 14px; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 1px;">Documento Disponível</p>
      <p style="color: #065f46; font-size: 18px; font-weight: 700; margin: 0;">{{document_name}}</p>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Prezado(a) <strong>{{client_name}}</strong>,</p>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Informamos que o documento <strong>{{document_name}}</strong> referente ao processo <strong>{{case_number}}</strong> está pronto e disponível para download no portal do cliente.</p>
    <div style="background: #f3f4f6; border-left: 4px solid #059669; padding: 16px; margin: 16px 0; border-radius: 0 4px 4px 0;">
      <p style="margin: 0 0 8px; color: #6b7280; font-size: 13px;">DOCUMENTO</p>
      <p style="margin: 0 0 12px; color: #1e3a5f; font-size: 16px; font-weight: 600;">{{document_name}}</p>
      <p style="margin: 0 0 8px; color: #6b7280; font-size: 13px;">PROCESSO</p>
      <p style="margin: 0; color: #1e3a5f; font-size: 16px; font-weight: 600;">{{case_number}}</p>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 16px 0;">Caso precise de esclarecimentos sobre o documento, entre em contato com <strong>{{lawyer_name}}</strong>.</p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="#" style="background: #059669; color: #ffffff; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block;">Baixar Documento</a>
    </div>
  </div>
  <div style="background: #f9fafb; padding: 24px; text-align: center; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="color: #6b7280; font-size: 13px; margin: 0 0 4px;">{{office_name}}</p>
    <p style="color: #9ca3af; font-size: 12px; margin: 0 0 4px;">Tel: {{office_phone}} | E-mail: {{office_email}}</p>
    <p style="color: #9ca3af; font-size: 11px; margin: 12px 0 0;"><a href="#" style="color: #9ca3af;">Cancelar inscrição</a></p>
  </div>
</div>`,
  },
  {
    name: 'Fatura de Honorários',
    subject: 'Fatura {{invoice_number}} - Vencimento em {{due_date}}',
    category: 'invoice',
    variables: [
      { name: 'client_name', description: 'Nome do cliente' },
      { name: 'invoice_number', description: 'Número da fatura' },
      { name: 'invoice_amount', description: 'Valor da fatura' },
      { name: 'due_date', description: 'Data de vencimento' },
      { name: 'case_number', description: 'Número do processo' },
      { name: 'lawyer_name', description: 'Nome do advogado' },
      { name: 'office_name', description: 'Nome do escritório' },
      { name: 'office_phone', description: 'Telefone do escritório' },
      { name: 'office_email', description: 'E-mail do escritório' },
    ],
    body_html: `<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%); padding: 32px 24px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{{office_name}}</h1>
    <p style="color: #a3c4e8; margin: 8px 0 0; font-size: 14px;">Advocacia &amp; Consultoria Jurídica</p>
  </div>
  <div style="background: #ffffff; padding: 32px 24px; border: 1px solid #e5e7eb; border-top: none;">
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">Prezado(a) <strong>{{client_name}}</strong>,</p>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 24px;">Segue abaixo a fatura referente aos honorários advocatícios do processo <strong>{{case_number}}</strong>.</p>
    <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; margin: 0 0 24px;">
      <div style="background: #1e3a5f; padding: 12px 20px;">
        <p style="color: #ffffff; font-weight: 600; margin: 0; font-size: 15px;">Detalhes da Fatura</p>
      </div>
      <div style="padding: 20px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 10px 0; color: #6b7280; font-size: 14px; border-bottom: 1px solid #e5e7eb;">Número da Fatura</td>
            <td style="padding: 10px 0; color: #1e3a5f; font-weight: 600; text-align: right; border-bottom: 1px solid #e5e7eb;">{{invoice_number}}</td>
          </tr>
          <tr>
            <td style="padding: 10px 0; color: #6b7280; font-size: 14px; border-bottom: 1px solid #e5e7eb;">Processo</td>
            <td style="padding: 10px 0; color: #1e3a5f; font-weight: 600; text-align: right; border-bottom: 1px solid #e5e7eb;">{{case_number}}</td>
          </tr>
          <tr>
            <td style="padding: 10px 0; color: #6b7280; font-size: 14px; border-bottom: 1px solid #e5e7eb;">Vencimento</td>
            <td style="padding: 10px 0; color: #dc2626; font-weight: 600; text-align: right; border-bottom: 1px solid #e5e7eb;">{{due_date}}</td>
          </tr>
          <tr>
            <td style="padding: 12px 0; color: #374151; font-size: 16px; font-weight: 600;">Valor Total</td>
            <td style="padding: 12px 0; color: #1e3a5f; font-size: 22px; font-weight: 700; text-align: right;">{{invoice_amount}}</td>
          </tr>
        </table>
      </div>
    </div>
    <p style="color: #374151; line-height: 1.6; margin: 0 0 16px;">O pagamento pode ser realizado via PIX, transferência bancária ou boleto. Para obter os dados de pagamento, acesse o portal do cliente ou entre em contato com nosso escritório.</p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="#" style="background: #2d5a8e; color: #ffffff; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block;">Pagar Fatura</a>
    </div>
    <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 16px 0 0;">Advogado responsável: {{lawyer_name}}</p>
  </div>
  <div style="background: #f9fafb; padding: 24px; text-align: center; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
    <p style="color: #6b7280; font-size: 13px; margin: 0 0 4px;">{{office_name}}</p>
    <p style="color: #9ca3af; font-size: 12px; margin: 0 0 4px;">Tel: {{office_phone}} | E-mail: {{office_email}}</p>
    <p style="color: #9ca3af; font-size: 11px; margin: 12px 0 0;"><a href="#" style="color: #9ca3af;">Cancelar inscrição</a></p>
  </div>
</div>`,
  },
];

// ── Helpers ──

function CategoryBadge({ category }: { category: string }) {
  const cfg = categoryConfig[category] ?? { label: category, className: 'bg-gray-100 text-gray-700', icon: <FileText className="h-3.5 w-3.5" /> };
  return (
    <Badge variant="outline" className={`${cfg.className} flex items-center gap-1`}>
      {cfg.icon}
      {cfg.label}
    </Badge>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR');
}

function replaceVariables(text: string, vars: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (match, key) => vars[key] || match);
}

function extractPreviewSnippet(html: string): string {
  const stripped = html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  return stripped.substring(0, 120) + (stripped.length > 120 ? '...' : '');
}

function getCategoryIcon(category: string) {
  const cfg = categoryConfig[category];
  return cfg?.icon || <FileText className="h-4 w-4" />;
}

// ── Variable Chip Insert ──

function VariableChips({ onInsert }: { onInsert: (variable: string) => void }) {
  return (
    <TooltipProvider>
      <div className="flex flex-wrap gap-1.5">
        {availableVariables.map((v) => (
          <Tooltip key={v.name}>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={() => onInsert(`{{${v.name}}}`)}
                className="inline-flex items-center gap-1 rounded-md border border-dashed border-muted-foreground/40 bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground hover:bg-muted hover:border-primary/50 hover:text-primary transition-colors cursor-pointer"
              >
                <Code className="h-2.5 w-2.5" />
                {`{{${v.name}}}`}
              </button>
            </TooltipTrigger>
            <TooltipContent side="top">
              <p>{v.description}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}

// ── Variable Input ──

function VariablesList({
  variables,
  onChange,
}: {
  variables: TemplateVariable[];
  onChange: (vars: TemplateVariable[]) => void;
}) {
  const addVariable = () => onChange([...variables, { name: '', description: '' }]);
  const removeVariable = (idx: number) => onChange(variables.filter((_, i) => i !== idx));
  const updateVariable = (idx: number, field: keyof TemplateVariable, value: string) => {
    const updated = [...variables];
    updated[idx] = { ...updated[idx], [field]: value };
    onChange(updated);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">Variáveis do Template</Label>
        <Button type="button" variant="outline" size="sm" onClick={addVariable}>
          <Plus className="mr-1 h-3 w-3" /> Adicionar
        </Button>
      </div>
      {variables.length === 0 && (
        <p className="text-xs text-muted-foreground italic">Nenhuma variável adicionada. Clique em &quot;Adicionar&quot; ou use os chips acima para inserir variáveis no corpo do e-mail.</p>
      )}
      {variables.map((v, idx) => (
        <div key={idx} className="flex gap-2 items-center">
          <div className="flex items-center gap-1 min-w-0 flex-1">
            <span className="text-xs text-muted-foreground shrink-0">{'{{'}</span>
            <Input
              placeholder="nome_variavel"
              value={v.name}
              onChange={(e) => updateVariable(idx, 'name', e.target.value)}
              className="flex-1 h-8 text-sm"
            />
            <span className="text-xs text-muted-foreground shrink-0">{'}}'}</span>
          </div>
          <Input
            placeholder="Descrição"
            value={v.description}
            onChange={(e) => updateVariable(idx, 'description', e.target.value)}
            className="flex-1 h-8 text-sm"
          />
          <Button type="button" variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={() => removeVariable(idx)} aria-label="Remover variável">
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      ))}
    </div>
  );
}

// ── Email Preview Renderer ──

function EmailPreview({ html, subject }: { html: string; subject: string }) {
  const renderedHtml = replaceVariables(html, sampleData);
  const renderedSubject = replaceVariables(subject, sampleData);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2">
        <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-xs text-muted-foreground">Assunto:</p>
          <p className="text-sm font-medium truncate">{renderedSubject}</p>
        </div>
      </div>
      <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
        <div
          className="p-4"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(renderedHtml) }}
        />
      </div>
      <p className="text-[10px] text-muted-foreground text-center italic">
        Pré-visualização com dados de exemplo. As variáveis serão substituídas com dados reais ao enviar.
      </p>
    </div>
  );
}

// ── Template Editor (Full Page Section) ──

function TemplateEditor({
  template,
  onClose,
}: {
  template?: EmailTemplate;
  onClose: () => void;
}) {
  const [name, setName] = useState(template?.name || '');
  const [subject, setSubject] = useState(template?.subject || '');
  const [category, setCategory] = useState(template?.category || 'welcome');
  const [bodyHtml, setBodyHtml] = useState(template?.body_html || '');
  const [variables, setVariables] = useState<TemplateVariable[]>(template?.variables || []);
  const [aiDescription, setAiDescription] = useState('');
  const [editorTab, setEditorTab] = useState<string>('editor');

  const createTemplate = useCreateEmailTemplate();
  const updateTemplate = useUpdateEmailTemplate();
  const generateAI = useGenerateEmailTemplateAI();

  const isEditing = !!template;
  const isPending = createTemplate.isPending || updateTemplate.isPending;

  const handleSubmit = () => {
    const data = { name, subject, category, body_html: bodyHtml, variables };
    if (isEditing) {
      updateTemplate.mutate(
        { id: template.id, data },
        { onSuccess: () => onClose() }
      );
    } else {
      createTemplate.mutate(data, { onSuccess: () => onClose() });
    }
  };

  const handleGenerateAI = () => {
    generateAI.mutate(
      { description: aiDescription, category },
      {
        onSuccess: (data) => {
          if (data.name) setName(data.name);
          if (data.subject) setSubject(data.subject);
          if (data.body_html) setBodyHtml(data.body_html);
          if (data.variables) setVariables(data.variables);
          setAiDescription('');
        },
      }
    );
  };

  const handleInsertVariable = (variable: string) => {
    setBodyHtml((prev) => prev + variable);
    // Auto-add to variables list if not present
    const varName = variable.replace(/[{}]/g, '');
    const exists = variables.some((v) => v.name === varName);
    if (!exists) {
      const known = availableVariables.find((v) => v.name === varName);
      setVariables((prev) => [...prev, { name: varName, description: known?.description || '' }]);
    }
  };

  const handleLoadPrebuilt = (pb: PrebuiltTemplate) => {
    setName(pb.name);
    setSubject(pb.subject);
    setCategory(pb.category);
    setBodyHtml(pb.body_html);
    setVariables(pb.variables);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onClose} className="gap-1">
            <ChevronRight className="h-4 w-4 rotate-180" /> Voltar
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <h2 className="text-lg font-semibold">
            {isEditing ? 'Editar Template' : 'Novo Template de E-mail'}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!name || !subject || isPending}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditing ? 'Salvar Alterações' : 'Criar Template'}
          </Button>
        </div>
      </div>

      {/* AI Generation Bar */}
      <Card className="border-dashed border-primary/30 bg-primary/5">
        <CardContent className="py-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
              <span className="text-sm font-medium hidden sm:inline">Gerar com IA</span>
            </div>
            <Input
              placeholder="Descreva o e-mail que deseja criar... Ex: 'E-mail avisando cliente sobre nova movimentação processual'"
              value={aiDescription}
              onChange={(e) => setAiDescription(e.target.value)}
              className="flex-1"
            />
            <Button
              onClick={handleGenerateAI}
              disabled={!aiDescription || generateAI.isPending}
              className="shrink-0"
            >
              {generateAI.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <Sparkles className="h-4 w-4 mr-1" />
              )}
              Gerar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Editor Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Editor */}
        <div className="space-y-4">
          {/* Template Info */}
          <Card>
            <CardContent className="pt-4 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-sm">Nome do Template</Label>
                  <AIInput
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    setValue={setName}
                    placeholder="Ex: Boas-vindas ao Cliente"
                    aiContext="Nome de um template de e-mail jurídico reutilizável"
                    aiObjective="Sugerir um nome descritivo e profissional para o template em português"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm">Categoria</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {Object.entries(categoryConfig).map(([k, v]) => (
                        <SelectItem key={k} value={k}>
                          <span className="flex items-center gap-2">{v.icon} {v.label}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className="text-sm">Assunto do E-mail</Label>
                <AIInput
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  setValue={setSubject}
                  placeholder="Ex: Bem-vindo(a) ao {{office_name}}, {{client_name}}!"
                  aiContext="Linha de assunto de um e-mail jurídico enviado a clientes ou partes do processo"
                  aiObjective="Sugerir ou melhorar o assunto do e-mail para ser claro, profissional e persuasivo"
                />
              </div>
            </CardContent>
          </Card>

          {/* Body Editor with Tabs */}
          <Card>
            <CardContent className="pt-4 space-y-3">
              <Tabs value={editorTab} onValueChange={setEditorTab}>
                <div className="flex items-center justify-between">
                  <TabsList>
                    <TabsTrigger value="editor" className="gap-1.5">
                      <Code className="h-3.5 w-3.5" /> HTML
                    </TabsTrigger>
                    <TabsTrigger value="templates" className="gap-1.5">
                      <LayoutTemplate className="h-3.5 w-3.5" /> Modelos Prontos
                    </TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="editor" className="space-y-3 mt-3">
                  {/* Variable Chips */}
                  <div className="space-y-1.5">
                    <Label className="text-xs text-muted-foreground">Clique para inserir variável:</Label>
                    <VariableChips onInsert={handleInsertVariable} />
                  </div>
                  <AITextarea
                    value={bodyHtml}
                    onChange={(e) => setBodyHtml(e.target.value)}
                    setValue={setBodyHtml}
                    placeholder='<div style="font-family: Arial, sans-serif;">&#10;  <h1>Titulo</h1>&#10;  <p>Prezado(a) {{client_name}},</p>&#10;  <p>Conteudo do e-mail...</p>&#10;</div>'
                    rows={16}
                    className="font-mono text-xs leading-relaxed"
                    aiContext="Corpo HTML de um template de e-mail jurídico com variáveis dinâmicas como {{client_name}}, {{case_number}}"
                    aiObjective="Melhorar o conteúdo textual do e-mail, corrigir português e aprimorar a comunicação jurídica profissional"
                  />
                </TabsContent>

                <TabsContent value="templates" className="mt-3">
                  <div className="grid gap-2">
                    {prebuiltTemplates.map((pb, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleLoadPrebuilt(pb)}
                        className="flex items-start gap-3 rounded-lg border p-3 text-left hover:bg-muted/50 transition-colors w-full"
                      >
                        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center shrink-0 mt-0.5">
                          {getCategoryIcon(pb.category)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-sm">{pb.name}</p>
                            <CategoryBadge category={pb.category} />
                          </div>
                          <p className="text-xs text-muted-foreground mt-0.5 truncate">{pb.subject}</p>
                          <p className="text-[11px] text-muted-foreground/70 mt-1">
                            {pb.variables.length} variáveis | {extractPreviewSnippet(pb.body_html).substring(0, 80)}...
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
                      </button>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Variables List */}
          <Card>
            <CardContent className="pt-4">
              <VariablesList variables={variables} onChange={setVariables} />
            </CardContent>
          </Card>
        </div>

        {/* Right: Preview */}
        <div className="space-y-3">
          <Card className="sticky top-4">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Pré-visualização do E-mail
              </CardTitle>
            </CardHeader>
            <CardContent>
              {bodyHtml ? (
                <ScrollArea className="h-[calc(100vh-320px)] pr-2">
                  <EmailPreview html={bodyHtml} subject={subject || '(Sem assunto)'} />
                </ScrollArea>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <Eye className="h-10 w-10 mb-3 opacity-30" />
                  <p className="text-sm">Escreva o HTML do e-mail ou selecione um modelo pronto para ver a pré-visualização aqui.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ── Preview Dialog (for list view) ──

function PreviewDialog({ template }: { template: EmailTemplate }) {
  const [open, setOpen] = useState(false);
  const [variableValues, setVariableValues] = useState<Record<string, string>>({});
  const [useCustom, setUseCustom] = useState(false);
  const preview = usePreviewEmailTemplate();

  const handlePreview = () => {
    preview.mutate({ template_id: template.id, variables: variableValues });
  };

  const displayHtml = useCustom && preview.data
    ? preview.data.body_html
    : replaceVariables(template.body_html, sampleData);
  const displaySubject = useCustom && preview.data
    ? preview.data.subject
    : replaceVariables(template.subject, sampleData);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Pré-visualizar template"><Eye className="h-4 w-4" /></Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Preview: {template.name}
          </DialogTitle>
          <DialogDescription className="sr-only">Pré-visualização do template de e-mail</DialogDescription>
        </DialogHeader>

        {template.variables.length > 0 && (
          <div className="space-y-3 border rounded-lg p-3 bg-muted/30">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Variáveis personalizadas</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setUseCustom(!useCustom)}
              >
                {useCustom ? 'Usar dados de exemplo' : 'Personalizar variáveis'}
              </Button>
            </div>
            {useCustom && (
              <>
                {template.variables.map((v) => (
                  <div key={v.name} className="flex gap-2 items-center">
                    <Label className="w-32 text-xs font-mono">{`{{${v.name}}}`}</Label>
                    <Input
                      placeholder={v.description}
                      value={variableValues[v.name] || ''}
                      onChange={(e) => setVariableValues({ ...variableValues, [v.name]: e.target.value })}
                      className="flex-1 h-8 text-sm"
                    />
                  </div>
                ))}
                <Button onClick={handlePreview} disabled={preview.isPending} size="sm">
                  {preview.isPending ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Eye className="mr-1 h-3 w-3" />}
                  Renderizar
                </Button>
              </>
            )}
          </div>
        )}

        <div className="space-y-3">
          <div className="flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Assunto:</p>
              <p className="text-sm font-medium">{displaySubject}</p>
            </div>
          </div>
          <div className="rounded-lg border bg-white shadow-sm overflow-hidden">
            <div
              className="p-4"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(displayHtml) }}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Template Card (Grid Item) ──

function TemplateCard({
  template,
  onEdit,
  onDelete,
}: {
  template: EmailTemplate;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const snippet = extractPreviewSnippet(template.body_html);

  return (
    <Card className="group hover:shadow-md transition-shadow">
      {/* Thumbnail Preview */}
      <div className="h-36 overflow-hidden rounded-t-lg border-b bg-white relative">
        <div
          className="transform scale-[0.35] origin-top-left w-[285%] h-[285%] pointer-events-none p-2"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(replaceVariables(template.body_html, sampleData)) }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-white/80" />
      </div>

      <CardContent className="pt-3 pb-4 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-sm truncate">{template.name}</h3>
            <p className="text-xs text-muted-foreground truncate mt-0.5">{template.subject}</p>
          </div>
          <CategoryBadge category={template.category} />
        </div>

        <p className="text-[11px] text-muted-foreground line-clamp-2">{snippet}</p>

        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            <span>{template.variables_count} var.</span>
            <span>|</span>
            <span>{formatDate(template.created_at)}</span>
          </div>
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <PreviewDialog template={template} />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onEdit}>
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Editar</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onDelete}>
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Excluir</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Page ──

export default function EmailTemplatesPage() {
  const { data: templates, isLoading } = useEmailTemplates();
  const deleteTemplate = useDeleteEmailTemplate();
  const [view, setView] = useState<'list' | 'editor'>('list');
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');

  const filteredTemplates = useMemo(() => {
    if (!templates) return [];
    return templates.filter((t) => {
      const matchesSearch = !searchQuery ||
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.subject.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = filterCategory === 'all' || t.category === filterCategory;
      return matchesSearch && matchesCategory;
    });
  }, [templates, searchQuery, filterCategory]);

  const handleNewTemplate = () => {
    setEditingTemplate(undefined);
    setView('editor');
  };

  const handleEditTemplate = (t: EmailTemplate) => {
    setEditingTemplate(t);
    setView('editor');
  };

  const handleCloseEditor = () => {
    setView('list');
    setEditingTemplate(undefined);
  };

  // Editor View
  if (view === 'editor') {
    return (
      <div className="space-y-6">
        <TemplateEditor template={editingTemplate} onClose={handleCloseEditor} />
      </div>
    );
  }

  // List View
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Mail className="h-6 w-6" /> Templates de E-mail
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie templates de e-mail reutilizáveis com variáveis dinâmicas e pré-visualização em tempo real
          </p>
        </div>
        <Button onClick={handleNewTemplate} className="shrink-0">
          <Plus className="mr-2 h-4 w-4" /> Novo Template
        </Button>
      </div>

      {/* Stats Bar */}
      {templates && templates.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card>
            <CardContent className="py-3 flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-blue-100 flex items-center justify-center">
                <LayoutTemplate className="h-4.5 w-4.5 text-blue-700" />
              </div>
              <div>
                <p className="text-xl font-bold">{templates.length}</p>
                <p className="text-[11px] text-muted-foreground">Templates</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-3 flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-emerald-100 flex items-center justify-center">
                <UserPlus className="h-4.5 w-4.5 text-emerald-700" />
              </div>
              <div>
                <p className="text-xl font-bold">{templates.filter(t => t.category === 'welcome' || t.category === 'client').length}</p>
                <p className="text-[11px] text-muted-foreground">Boas-vindas</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-3 flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-red-100 flex items-center justify-center">
                <Clock className="h-4.5 w-4.5 text-red-700" />
              </div>
              <div>
                <p className="text-xl font-bold">{templates.filter(t => t.category === 'deadline_reminder' || t.category === 'deadline').length}</p>
                <p className="text-[11px] text-muted-foreground">Prazos</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-3 flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-amber-100 flex items-center justify-center">
                <Receipt className="h-4.5 w-4.5 text-amber-700" />
              </div>
              <div>
                <p className="text-xl font-bold">{templates.filter(t => t.category === 'invoice' || t.category === 'billing').length}</p>
                <p className="text-[11px] text-muted-foreground">Faturas</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Todas categorias" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas categorias</SelectItem>
            {Object.entries(categoryConfig).map(([k, v]) => (
              <SelectItem key={k} value={k}>
                <span className="flex items-center gap-2">{v.icon} {v.label}</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <div className="p-4 space-y-3">
                <Skeleton className="h-32 w-full rounded" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </Card>
          ))}
        </div>
      ) : !templates?.length ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Mail className="h-12 w-12 mx-auto mb-4 text-muted-foreground/30" />
            <h3 className="text-lg font-semibold mb-1">Nenhum template de e-mail</h3>
            <p className="text-sm text-muted-foreground mb-6">
              Crie seu primeiro template ou use um dos modelos prontos para começar.
            </p>
            <Button onClick={handleNewTemplate}>
              <Plus className="mr-2 h-4 w-4" /> Criar Primeiro Template
            </Button>
          </CardContent>
        </Card>
      ) : filteredTemplates.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            <Search className="h-8 w-8 mx-auto mb-3 opacity-30" />
            <p>Nenhum template encontrado com os filtros selecionados.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTemplates.map((t) => (
            <TemplateCard
              key={t.id}
              template={t}
              onEdit={() => handleEditTemplate(t)}
              onDelete={() => deleteTemplate.mutate(t.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
