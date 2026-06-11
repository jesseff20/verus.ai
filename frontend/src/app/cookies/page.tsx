'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Cookie,
  ChevronLeft,
  Download,
  Printer,
  ShieldCheck,
  AlertTriangle,
  Info,
  XCircle,
  CheckCircle2,
  Settings2,
  SlidersHorizontal,
  Shield,
  Eye,
  BarChart3,
  Users,
  Globe,
  Smartphone,
  ArrowRight,
} from 'lucide-react';

// ─── Tipos ──────────────────────────────────────────────────────────────────

interface CookieInfo {
  nome: string;
  finalidade: string;
  duracao: string;
  tipo: 'essencial' | 'funcional' | 'analytics' | 'marketing';
  dominio: string;
}

// ─── Dados ──────────────────────────────────────────────────────────────────

const cookiesList: CookieInfo[] = [
  // Essenciais
  {
    nome: '__session',
    finalidade: 'Gerenciar a sessão do usuário autenticado na plataforma.',
    duracao: 'Sessão',
    tipo: 'essencial',
    dominio: 'verus.ai',
  },
  {
    nome: 'XSRF-TOKEN',
    finalidade: 'Proteger contra ataques CSRF (Cross-Site Request Forgery).',
    duracao: 'Sessão',
    tipo: 'essencial',
    dominio: 'verus.ai',
  },
  {
    nome: 'next-auth.session-token',
    finalidade: 'Armazenar o token de autenticação JWT do usuário.',
    duracao: '30 dias',
    tipo: 'essencial',
    dominio: 'verus.ai',
  },
  {
    nome: 'verus-theme',
    finalidade: 'Armazenar a preferência de tema (claro/escuro) do usuário.',
    duracao: '1 ano',
    tipo: 'essencial',
    dominio: 'verus.ai',
  },
  {
    nome: 'cookie-consent',
    finalidade: 'Registrar as preferências de cookies do usuário.',
    duracao: '1 ano',
    tipo: 'essencial',
    dominio: 'verus.ai',
  },
  {
    nome: '__cf_bm',
    finalidade: 'Proteção contra bots e ataques DDoS (Cloudflare).',
    duracao: '30 minutos',
    tipo: 'essencial',
    dominio: '.verus.ai',
  },

  // Funcionais
  {
    nome: 'client_portal_access_token',
    finalidade: 'Manter a sessão do portal do cliente autenticado.',
    duracao: '24 horas',
    tipo: 'funcional',
    dominio: 'verus.ai',
  },
  {
    nome: 'previous_page',
    finalidade: 'Armazenar a última página visitada para navegação de voltar.',
    duracao: 'Sessão',
    tipo: 'funcional',
    dominio: 'verus.ai',
  },

  // Analytics
  {
    nome: '_ga',
    finalidade: 'Distinguir usuários únicos (Google Analytics 4).',
    duracao: '2 anos',
    tipo: 'analytics',
    dominio: '.verus.ai',
  },
  {
    nome: '_ga_XXXXXXXXXX',
    finalidade: 'Distinguir sessões do usuário no GA4.',
    duracao: '2 anos',
    tipo: 'analytics',
    dominio: '.verus.ai',
  },
  {
    nome: '_gid',
    finalidade: 'Distinguir usuários (24h) para relatórios de audiência.',
    duracao: '24 horas',
    tipo: 'analytics',
    dominio: '.verus.ai',
  },
  {
    nome: '_gat_gtag',
    finalidade: 'Limitar a taxa de requisições ao Google Analytics.',
    duracao: '1 minuto',
    tipo: 'analytics',
    dominio: '.verus.ai',
  },
  {
    nome: 'plausible_visit',
    finalidade: 'Rastrear visitas anônimas via Plausible Analytics (sem cookies cross-site).',
    duracao: '1 hora',
    tipo: 'analytics',
    dominio: 'verus.ai',
  },

  // Marketing
  {
    nome: '_fbp',
    finalidade: 'Rastrear visitas para campanhas de anúncios no Facebook/Instagram.',
    duracao: '3 meses',
    tipo: 'marketing',
    dominio: '.verus.ai',
  },
  {
    nome: '_gcl_au',
    finalidade: 'Rastrear conversões de anúncios do Google Ads.',
    duracao: '3 meses',
    tipo: 'marketing',
    dominio: '.verus.ai',
  },
  {
    nome: 'linkedin_analytics',
    finalidade: 'Rastrear visitas e conversões de campanhas no LinkedIn.',
    duracao: '3 meses',
    tipo: 'marketing',
    dominio: '.verus.ai',
  },
];

// ─── Helpers ────────────────────────────────────────────────────────────────

function tipoIcon(tipo: CookieInfo['tipo']) {
  switch (tipo) {
    case 'essencial': return ShieldCheck;
    case 'funcional': return Settings2;
    case 'analytics': return BarChart3;
    case 'marketing': return Users;
  }
}

function tipoColor(tipo: CookieInfo['tipo']) {
  switch (tipo) {
    case 'essencial': return 'text-green-700 bg-green-50 border-green-200';
    case 'funcional': return 'text-blue-700 bg-blue-50 border-blue-200';
    case 'analytics': return 'text-amber-700 bg-amber-50 border-amber-200';
    case 'marketing': return 'text-purple-700 bg-purple-50 border-purple-200';
  }
}

function tipoLabel(tipo: CookieInfo['tipo']) {
  switch (tipo) {
    case 'essencial': return 'Essencial';
    case 'funcional': return 'Funcional';
    case 'analytics': return 'Analytics';
    case 'marketing': return 'Marketing';
  }
}

// ─── Component ──────────────────────────────────────────────────────────────

export default function CookiesPage() {
  const [showPrint, setShowPrint] = useState(false);
  const [simulatedPrefs, setSimulatedPrefs] = useState({
    essencial: true,
    funcional: true,
    analytics: false,
    marketing: false,
  });

  const lastUpdate = '15 de janeiro de 2026';

  const handlePrint = () => window.print();

  const handlePrefToggle = (category: keyof typeof simulatedPrefs) => {
    if (category === 'essencial') return; // can't disable essential
    setSimulatedPrefs((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50/30">
      {/* ── Top bar ── */}
      <div className="sticky top-0 z-40 border-b border-purple-100/80 bg-white/90 backdrop-blur-md no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-[#7030A0] transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            Voltar ao início
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handlePrint} className="text-xs gap-1.5">
              <Printer className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Imprimir</span>
            </Button>
            <Button variant="outline" size="sm" className="text-xs gap-1.5">
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Download PDF</span>
            </Button>
          </div>
        </div>
      </div>

      {/* ── Header ── */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 pb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7030A0]/10">
            <Cookie className="h-5 w-5 text-[#7030A0]" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Política de Cookies
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Última atualização: {lastUpdate}
            </p>
          </div>
        </div>

        <Card className="mt-6 border-2 border-[#7030A0]/20 bg-gradient-to-r from-[#7030A0]/5 to-purple-50/50">
          <CardContent className="p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-[#7030A0] shrink-0 mt-0.5" />
              <div className="text-sm text-gray-700 leading-relaxed">
                Esta Política de Cookies explica o que são cookies, como os utilizamos na
                plataforma Verus.AI e como você pode gerenciar suas preferências. Esta
                política complementa nossa{' '}
                <Link href="/privacidade" className="text-[#7030A0] font-medium hover:underline">
                  Política de Privacidade
                </Link>
                .
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Content ── */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 pb-16 space-y-6">

        {/* 1. O que são cookies */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Cookie className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                1. O que são Cookies?
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Cookies são pequenos arquivos de texto armazenados no seu navegador ou
                dispositivo quando você visita um site. Eles permitem que o site reconheça
                seu dispositivo, armazene preferências e ofereça uma experiência
                personalizada.
              </p>
              <p className="text-sm text-gray-600 leading-relaxed mt-2">
                Os cookies podem ser classificados como:
              </p>
              <ul className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                <li className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-green-50 border border-green-100">
                  <Shield className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-gray-800">Essenciais:</strong> necessários para
                    o funcionamento básico do site.
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-blue-50 border border-blue-100">
                  <Settings2 className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-gray-800">Funcionais:</strong> permitem
                    funcionalidades adicionais e preferências.
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-amber-50 border border-amber-100">
                  <BarChart3 className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-gray-800">Analytics:</strong> coletam dados
                    anônimos de uso para melhoria do serviço.
                  </span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-purple-50 border border-purple-100">
                  <Users className="h-4 w-4 text-purple-600 mt-0.5 shrink-0" />
                  <span>
                    <strong className="text-gray-800">Marketing:</strong> rastreiam
                    visitas para campanhas publicitárias direcionadas.
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 2. Cookies essenciais vs não essenciais */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <AlertTriangle className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                2. Cookies Essenciais vs. Não Essenciais
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                A distinção entre cookies essenciais e não essenciais é fundamental para a
                conformidade com a LGPD e a privacidade do usuário:
              </p>

              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="rounded-xl border-2 border-green-200 bg-green-50/50 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <h3 className="text-sm font-semibold text-green-800">Essenciais</h3>
                  </div>
                  <ul className="space-y-1.5 text-xs text-green-700">
                    <li>• Necessários para o funcionamento do site</li>
                    <li>• Base legal: legítimo interesse (art. 10 LGPD)</li>
                    <li>• Não requerem consentimento prévio</li>
                    <li>• Não podem ser desativados pelo usuário</li>
                    <li>• Exemplos: autenticação, segurança, sessão</li>
                  </ul>
                </div>

                <div className="rounded-xl border-2 border-purple-200 bg-purple-50/50 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <XCircle className="h-5 w-5 text-purple-600" />
                    <h3 className="text-sm font-semibold text-purple-800">Não Essenciais</h3>
                  </div>
                  <ul className="space-y-1.5 text-xs text-purple-700">
                    <li>• Não são necessários para o funcionamento básico</li>
                    <li>• Base legal: consentimento (art. 7º, I, LGPD)</li>
                    <li>• Requerem opt-in explícito do usuário</li>
                    <li>• Podem ser ativados/desativados a qualquer momento</li>
                    <li>• Exemplos: analytics, marketing, redes sociais</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Lista completa de cookies */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Globe className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                3. Lista Completa de Cookies Utilizados
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Abaixo, listamos todos os cookies utilizados no Verus.AI, organizados por
                categoria, com nome, finalidade, duração e tipo.
              </p>

              {/* Essenciais */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="h-4 w-4 text-green-600" />
                  <h3 className="text-sm font-semibold text-gray-800">
                    Cookies Essenciais ({cookiesList.filter((c) => c.tipo === 'essencial').length})
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-green-200 bg-green-50/50">
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Nome</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Finalidade</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Duração</th>
                        <th className="text-left py-2 font-medium text-gray-700">Domínio</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-green-50">
                      {cookiesList.filter((c) => c.tipo === 'essencial').map((c) => (
                        <tr key={c.nome} className="hover:bg-green-50/30">
                          <td className="py-2 pr-2 font-mono text-[11px] text-gray-800 whitespace-nowrap">{c.nome}</td>
                          <td className="py-2 pr-2 text-gray-600">{c.finalidade}</td>
                          <td className="py-2 pr-2 text-gray-500 whitespace-nowrap">{c.duracao}</td>
                          <td className="py-2 text-gray-500 font-mono text-[11px] whitespace-nowrap">{c.dominio}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Funcionais */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <Settings2 className="h-4 w-4 text-blue-600" />
                  <h3 className="text-sm font-semibold text-gray-800">
                    Cookies Funcionais ({cookiesList.filter((c) => c.tipo === 'funcional').length})
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-blue-200 bg-blue-50/50">
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Nome</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Finalidade</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Duração</th>
                        <th className="text-left py-2 font-medium text-gray-700">Domínio</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-blue-50">
                      {cookiesList.filter((c) => c.tipo === 'funcional').map((c) => (
                        <tr key={c.nome} className="hover:bg-blue-50/30">
                          <td className="py-2 pr-2 font-mono text-[11px] text-gray-800 whitespace-nowrap">{c.nome}</td>
                          <td className="py-2 pr-2 text-gray-600">{c.finalidade}</td>
                          <td className="py-2 pr-2 text-gray-500 whitespace-nowrap">{c.duracao}</td>
                          <td className="py-2 text-gray-500 font-mono text-[11px] whitespace-nowrap">{c.dominio}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Analytics */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="h-4 w-4 text-amber-600" />
                  <h3 className="text-sm font-semibold text-gray-800">
                    Cookies de Analytics ({cookiesList.filter((c) => c.tipo === 'analytics').length})
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-amber-200 bg-amber-50/50">
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Nome</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Finalidade</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Duração</th>
                        <th className="text-left py-2 font-medium text-gray-700">Domínio</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-amber-50">
                      {cookiesList.filter((c) => c.tipo === 'analytics').map((c) => (
                        <tr key={c.nome} className="hover:bg-amber-50/30">
                          <td className="py-2 pr-2 font-mono text-[11px] text-gray-800 whitespace-nowrap">{c.nome}</td>
                          <td className="py-2 pr-2 text-gray-600">{c.finalidade}</td>
                          <td className="py-2 pr-2 text-gray-500 whitespace-nowrap">{c.duracao}</td>
                          <td className="py-2 text-gray-500 font-mono text-[11px] whitespace-nowrap">{c.dominio}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Marketing */}
              <div className="mb-2">
                <div className="flex items-center gap-2 mb-3">
                  <Users className="h-4 w-4 text-purple-600" />
                  <h3 className="text-sm font-semibold text-gray-800">
                    Cookies de Marketing ({cookiesList.filter((c) => c.tipo === 'marketing').length})
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-purple-200 bg-purple-50/50">
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Nome</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Finalidade</th>
                        <th className="text-left py-2 pr-2 font-medium text-gray-700">Duração</th>
                        <th className="text-left py-2 font-medium text-gray-700">Domínio</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-purple-50">
                      {cookiesList.filter((c) => c.tipo === 'marketing').map((c) => (
                        <tr key={c.nome} className="hover:bg-purple-50/30">
                          <td className="py-2 pr-2 font-mono text-[11px] text-gray-800 whitespace-nowrap">{c.nome}</td>
                          <td className="py-2 pr-2 text-gray-600">{c.finalidade}</td>
                          <td className="py-2 pr-2 text-gray-500 whitespace-nowrap">{c.duracao}</td>
                          <td className="py-2 text-gray-500 font-mono text-[11px] whitespace-nowrap">{c.dominio}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <p className="text-xs text-gray-400 mt-4">
                Total: {cookiesList.length} cookies — {cookiesList.filter((c) => c.tipo === 'essencial').length} essenciais,{' '}
                {cookiesList.filter((c) => c.tipo === 'funcional').length} funcionais,{' '}
                {cookiesList.filter((c) => c.tipo === 'analytics').length} de analytics,{' '}
                {cookiesList.filter((c) => c.tipo === 'marketing').length} de marketing.
              </p>
            </div>
          </div>
        </div>

        {/* 4. Gerenciamento de Preferências */}
        <div className="rounded-2xl border-2 border-[#7030A0]/20 bg-gradient-to-br from-[#7030A0]/5 to-purple-50/50 p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <SlidersHorizontal className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                4. Gerenciamento de Preferências de Cookies
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Você pode gerenciar suas preferências de cookies a qualquer momento.
                Abaixo está uma simulação do painel de controle de preferências que será
                exibido no banner de cookies do Verus.AI:
              </p>

              <div className="rounded-xl bg-white border border-purple-100 p-4 sm:p-5 space-y-3">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Suas Preferências
                </p>

                {([
                  { key: 'essencial' as const, label: 'Essenciais', desc: 'Necessários para o funcionamento básico da plataforma.' },
                  { key: 'funcional' as const, label: 'Funcionais', desc: 'Permitem funcionalidades adicionais e lembram suas preferências.' },
                  { key: 'analytics' as const, label: 'Analytics', desc: 'Coletam dados anônimos de uso para melhorarmos o serviço.' },
                  { key: 'marketing' as const, label: 'Marketing', desc: 'Rastreiam visitas para campanhas publicitárias direcionadas.' },
                ]).map(({ key, label, desc }) => (
                  <div
                    key={key}
                    className={`flex items-center justify-between gap-3 p-3 rounded-lg ${
                      key === 'essencial'
                        ? 'bg-gray-50 border border-gray-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-800">{label}</p>
                        <Badge
                          variant="outline"
                          className={`text-[10px] px-1.5 py-0 ${
                            key === 'essencial'
                              ? 'bg-green-50 text-green-700 border-green-200'
                              : simulatedPrefs[key]
                              ? 'bg-purple-50 text-purple-700 border-purple-200'
                              : 'bg-gray-100 text-gray-400 border-gray-200'
                          }`}
                        >
                          {simulatedPrefs[key] ? 'Ativo' : 'Inativo'}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                    </div>
                    <button
                      onClick={() => handlePrefToggle(key)}
                      disabled={key === 'essencial'}
                      className={`relative w-10 h-6 rounded-full transition-colors duration-200 ${
                        key === 'essencial'
                          ? 'bg-green-500 cursor-not-allowed opacity-60'
                          : simulatedPrefs[key]
                          ? 'bg-[#7030A0]'
                          : 'bg-gray-300'
                      }`}
                      aria-label={`Alternar cookies ${label}`}
                    >
                      <span
                        className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                          simulatedPrefs[key] ? 'translate-x-[18px]' : 'translate-x-[2px]'
                        }`}
                      />
                    </button>
                  </div>
                ))}

                <div className="pt-2 flex gap-2">
                  <Button className="flex-1 bg-gradient-to-r from-[#7030A0] to-[#5B2EE0] text-white text-xs">
                    Salvar Preferências
                  </Button>
                  <Button variant="outline" className="text-xs">
                    Aceitar Todos
                  </Button>
                  <Button variant="ghost" className="text-xs text-gray-500">
                    Recusar Todos
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 5. Opt-in */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <CheckCircle2 className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                5. Opt-in para Cookies Não Essenciais
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Em conformidade com o art. 7º, I, da LGPD e as diretrizes da ANPD sobre
                cookies, o Verus.AI adota o modelo de <strong>opt-in explícito</strong> para
                cookies não essenciais:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    Ao acessar a plataforma pela primeira vez, um <strong>banner de cookies</strong> é
                    exibido no topo ou rodapé da página.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    Nenhum cookie não essencial é carregado <strong>antes</strong> da sua
                    autorização explícita.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    Você pode <strong>aceitar, recusar ou personalizar</strong> cada
                    categoria de cookies.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    Sua escolha é registrada e respeitada por <strong>1 ano</strong>, ou até
                    que você limpe os cookies do navegador.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#7030A0] mt-0.5 shrink-0" />
                  <span>
                    Você pode <strong>alterar suas preferências</strong> a qualquer momento
                    através do link "Gerenciar Cookies" no rodapé do site ou nesta página.
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* 6. Consequências */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <AlertTriangle className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                6. Consequências de Desativar Cookies Essenciais
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Os cookies essenciais <strong>não podem ser desativados</strong> na
                plataforma Verus.AI, pois são necessários para:
              </p>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-red-50 border border-red-100">
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                  <span>Manter sua sessão autenticada com segurança</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-red-50 border border-red-100">
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                  <span>Proteger contra ataques CSRF e XSS</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-red-50 border border-red-100">
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                  <span>Armazenar preferências de tema e idioma</span>
                </div>
                <div className="flex items-start gap-2 text-sm text-gray-700 p-3 rounded-lg bg-red-50 border border-red-100">
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                  <span>Registrar suas escolhas de consentimento de cookies</span>
                </div>
              </div>
              <div className="mt-3 rounded-xl bg-red-50 border border-red-200 p-3">
                <p className="text-xs text-red-700">
                  <strong>Atenção:</strong> Se você desativar cookies essenciais nas
                  configurações do seu navegador, a plataforma Verus.AI pode não funcionar
                  corretamente ou pode ficar completamente inacessível. Recomendamos manter
                  cookies essenciais habilitados para o domínio verus.ai.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 7. Banner de Consentimento */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Smartphone className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                7. Banner de Consentimento de Cookies
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">
                Quando você acessa o Verus.AI pela primeira vez, o seguinte banner é
                exibido no canto inferior da tela:
              </p>

              {/* Simulated Banner */}
              <div className="rounded-xl border-2 border-[#7030A0]/30 bg-white shadow-lg p-4 sm:p-5 max-w-md mx-auto">
                <div className="flex items-start gap-3">
                  <Cookie className="h-5 w-5 text-[#7030A0] shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">Preferências de Cookies</p>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                      Utilizamos cookies essenciais para o funcionamento da plataforma e
                      cookies não essenciais para melhorar sua experiência. Para mais
                      detalhes, consulte nossa{' '}
                      <Link href="/cookies" className="text-[#7030A0] underline">
                        Política de Cookies
                      </Link>.
                    </p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      <Button size="sm" className="text-xs bg-gradient-to-r from-[#7030A0] to-[#5B2EE0] text-white">
                        Aceitar Todos
                      </Button>
                      <Button size="sm" variant="outline" className="text-xs">
                        Personalizar
                      </Button>
                      <Button size="sm" variant="ghost" className="text-xs text-gray-500">
                        Recusar
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-3">
                * Simulação do banner que será exibido. O design final pode variar.
              </p>
            </div>
          </div>
        </div>

        {/* 8. Atualizações */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Info className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                8. Atualizações desta Política
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Esta Política de Cookies pode ser atualizada para refletir mudanças nos
                cookies utilizados, na legislação aplicável ou nas práticas do mercado.
                Recomendamos a revisão periódica desta página.
              </p>
              <p className="text-sm text-gray-600 leading-relaxed mt-2">
                Em caso de alterações significativas, notificaremos os usuários por e-mail
                e por meio de um aviso na plataforma, solicitando novo consentimento quando
                necessário.
              </p>
            </div>
          </div>
        </div>

        {/* 9. Contato */}
        <div className="rounded-2xl border border-purple-100 bg-white p-5 sm:p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-9 h-9 rounded-lg bg-[#7030A0]/10 flex items-center justify-center">
              <Shield className="h-4.5 w-4.5 text-[#7030A0]" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                9. Contato do DPO
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                Se você tiver dúvidas sobre esta Política de Cookies ou sobre como tratamos
                seus dados pessoais, entre em contato com nosso Encarregado de Dados (DPO):
              </p>
              <div className="mt-3 rounded-xl bg-gray-50 border border-gray-200 p-4 space-y-1.5">
                <p className="text-sm text-gray-700">
                  <strong>E-mail:</strong>{' '}
                  <a href="mailto:dpo@verus.ai" className="text-[#7030A0] font-medium hover:underline">
                    dpo@verus.ai
                  </a>
                </p>
                <p className="text-sm text-gray-500">
                  Consulte também nossa{' '}
                  <Link href="/privacidade" className="text-[#7030A0] font-medium hover:underline">
                    Política de Privacidade
                  </Link>{' '}
                  para informações detalhadas.
                </p>
              </div>
            </div>
          </div>
        </div>

        <Separator className="bg-purple-100" />

        {/* Footer */}
        <div className="text-center space-y-3">
          <p className="text-xs text-gray-400">
            Versão 1.0 — Última atualização: {lastUpdate}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
            <Link href="/privacidade" className="text-[#7030A0] hover:underline font-medium">
              Política de Privacidade
            </Link>
            <span className="text-gray-300">•</span>
            <Link href="/consentimento" className="text-[#7030A0] hover:underline font-medium">
              Termo de Consentimento
            </Link>
            <span className="text-gray-300">•</span>
            <Link href="/" className="text-[#7030A0] hover:underline font-medium">
              Página Inicial
            </Link>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @media print {
          .sticky { display: none !important; }
          .no-print { display: none !important; }
          body { font-size: 11pt; color: #000; background: #fff; }
          .rounded-2xl { border: 1px solid #ddd; box-shadow: none; break-inside: avoid; }
        }
      `}</style>
    </div>
  );
}
