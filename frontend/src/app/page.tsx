'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight, GitBranch, Brain, ShieldCheck, FileText,
  Users, ChevronDown, CheckCircle2, Workflow, Zap, Scale,
  Building2, Timer, Lock, Database, Menu, X, Sun, Moon
} from 'lucide-react';

const SCHEDULE_URL = 'https://lgpdnow-4.youcanbook.me/';

/* ─── Theme hook (padrão: light) ───────────────────────────── */
function useLandingTheme() {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem('verus-landing-theme');
    if (saved === 'dark') setIsDark(true);
  }, []);
  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem('verus-landing-theme', next ? 'dark' : 'light');
  };
  return { isDark, toggle, mounted };
}

/* ─── Scroll reveal hook ───────────────────────────────────── */
function useReveal(threshold = 0.12) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

/* ─── Section wrapper ──────────────────────────────────────── */
function Section({
  children,
  className = '',
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  const { ref, visible } = useReveal();
  return (
    <section
      id={id}
      ref={ref}
      className={`transition-all duration-700 ease-out ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      } ${className}`}
    >
      {children}
    </section>
  );
}

/* ─── Data ─────────────────────────────────────────────────── */
const PROBLEMS = [
  {
    icon: FileText,
    title: 'Fluxos manuais e desconexos',
    desc: 'Petições, minutas e despachos transitam por e-mail, WhatsApp e papel. Nenhum rastreio estruturado.',
  },
  {
    icon: Timer,
    title: 'Controle de prazos fragmentado',
    desc: 'Prazos registrados em planilhas, agendas e cabeças individuais. Um deslize e o prazo cai.',
  },
  {
    icon: Users,
    title: 'Distribuição sem visibilidade',
    desc: 'O distribuidor não sabe a carga de cada procurador. Redistribuições e avocações sem histórico.',
  },
  {
    icon: Database,
    title: 'Conhecimento institucional perdido',
    desc: 'Pareceres, minutas e precedentes ficam em pastas locais. Novos membros reinventam o que já foi resolvido.',
  },
];

const FEATURES = [
  {
    icon: Workflow,
    color: '#7030A0',
    title: 'Fluxos BPMN por Procuradoria',
    desc: 'Editor visual de workflows com swim lanes por papel (Distribuidor, Procurador, Gerente, PG). Publique e execute fluxos completos — do recebimento ao arquivamento.',
  },
  {
    icon: Scale,
    color: '#5B2EE0',
    title: 'Gestão de Processos',
    desc: 'Processos judiciais e administrativos em um só lugar. Timeline de execução do fluxo, tarefas automáticas, prazos e histórico imutável.',
  },
  {
    icon: Brain,
    color: '#8B5CF6',
    title: 'IA Jurídica Especializada',
    desc: 'Geração de minutas, petições e despachos com contexto do processo. O assistente conhece o fluxo em que o processo está e sugere o documento correto.',
  },
  {
    icon: GitBranch,
    color: '#7030A0',
    title: 'Redistribuição e Avocação',
    desc: 'Solicitações de redistribuição passam pelo gerente. Avocação pelo PG/Subprocurador com registro formal. Tudo conforme o fluxo aprovado.',
  },
  {
    icon: ShieldCheck,
    color: '#5B2EE0',
    title: 'Segurança e Conformidade',
    desc: 'Isolamento completo de dados por órgão. LGPD nativo, auditoria de todas as ações, JWT de curta duração e controle de acesso por papel.',
  },
  {
    icon: Building2,
    color: '#8B5CF6',
    title: 'Multi-Órgão',
    desc: 'Um ambiente por procuradoria, completamente isolado. Cada órgão tem seus próprios fluxos, usuários e dados — sem interferência cruzada.',
  },
];

const FLOW_STEPS = [
  { role: 'Distribuidor(a)', action: 'Recebe e distribui o processo', color: '#7030A0' },
  { role: 'Procurador(a)', action: 'Elabora petição ou minuta', color: '#5B2EE0' },
  { role: 'Gerente', action: 'Revisa e encaminha para assinatura', color: '#8B5CF6' },
  { role: 'PG / Subprocurador', action: 'Assina despacho ou avoca', color: '#7030A0' },
  { role: 'Assessor(a)', action: 'Realiza peticionamento (PJe)', color: '#5B2EE0' },
];

/* ─── Main page ─────────────────────────────────────────────── */
export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { isDark, toggle, mounted } = useLandingTheme();

  const t = {
    /* backgrounds */
    bg:           isDark ? 'bg-[#0A0A0A]'            : 'bg-[#FAFAFA]',
    text:         isDark ? 'text-white'               : 'text-gray-900',
    muted:        isDark ? 'text-white/60'            : 'text-gray-500',
    faint:        isDark ? 'text-white/40'            : 'text-gray-400',
    /* nav */
    navBg:        isDark ? 'bg-[#0A0A0A]/85'          : 'bg-white/90',
    navBorder:    isDark ? 'border-white/5'           : 'border-gray-200',
    navLinks:     isDark ? 'text-white/60 hover:text-white' : 'text-gray-500 hover:text-gray-900',
    navEnter:     isDark ? 'text-white/60 hover:text-white' : 'text-gray-600 hover:text-gray-900',
    mobileBg:     isDark ? 'bg-[#0A0A0A]/98'          : 'bg-white/98',
    mobileDivider:isDark ? 'border-white/[0.06]'      : 'border-gray-100',
    mobileItem:   isDark ? 'text-white/70 hover:text-white border-white/[0.05]' : 'text-gray-600 hover:text-gray-900 border-gray-100',
    mobileLogin:  isDark ? 'text-white/60 border-white/10 hover:border-white/20 hover:text-white' : 'text-gray-600 border-gray-200 hover:border-gray-400 hover:text-gray-900',
    /* cards */
    card:         isDark ? 'border-white/6 bg-white/[0.02]'  : 'border-gray-200 bg-white',
    cardHover:    isDark ? 'hover:bg-white/[0.04] hover:border-white/10' : 'hover:shadow-md hover:border-gray-300',
    cardInner:    isDark ? 'border-white/6 bg-white/[0.03]'  : 'border-gray-200 bg-gray-50',
    iconBg:       isDark ? 'bg-[#7030A0]/15'          : 'bg-purple-100',
    /* section divider */
    divider:      isDark ? 'border-white/5'           : 'border-gray-100',
    /* IA cards */
    iaCard:       isDark ? 'border-[#7030A0]/20 bg-[#7030A0]/5 hover:bg-[#7030A0]/8 hover:border-[#7030A0]/35' : 'border-purple-200 bg-purple-50 hover:bg-purple-100 hover:border-purple-300',
    iaCaption:    isDark ? 'text-white/30'            : 'text-gray-400',
    iaBody:       isDark ? 'text-white/45'            : 'text-gray-600',
    iaTagColor:   isDark ? '#C084FC'                  : '#7030A0',
    iaTagBorder:  isDark ? 'rgba(112,48,160,0.25)'    : 'rgba(112,48,160,0.3)',
    iaTagBg:      isDark ? 'rgba(112,48,160,0.08)'    : 'rgba(112,48,160,0.06)',
    iaPanel:      isDark ? 'border-white/6 bg-white/[0.02]' : 'border-gray-200 bg-gray-50',
    /* flow viz */
    flowBorder:   isDark ? 'border-white/8 bg-white/[0.02]' : 'border-gray-200 bg-white',
    flowLine:     isDark ? 'bg-white/[0.08]'          : 'bg-gray-300',
    flowCaption:  isDark ? 'text-white/30'            : 'text-gray-400',
    flowRole:     isDark ? 'text-white/35'            : 'text-gray-400',
    /* CTA */
    ctaBorder:    isDark ? 'border-[#7030A0]/25'      : 'border-purple-200',
    ctaBg:        isDark
      ? 'radial-gradient(ellipse at center top, rgba(112,48,160,0.12) 0%, rgba(10,10,10,0) 70%)'
      : 'radial-gradient(ellipse at center top, rgba(112,48,160,0.07) 0%, rgba(250,250,250,0) 70%)',
    ctaInner:     isDark
      ? 'radial-gradient(ellipse at 50% 0%, rgba(91,46,224,0.08) 0%, transparent 70%)'
      : 'radial-gradient(ellipse at 50% 0%, rgba(91,46,224,0.04) 0%, transparent 70%)',
    ctaBody:      isDark ? 'text-white/50'            : 'text-gray-500',
    /* footer */
    footerCaption:isDark ? 'text-white/25'            : 'text-gray-400',
    footerLinks:  isDark ? 'text-white/30 hover:text-white/60' : 'text-gray-400 hover:text-gray-600',
    /* secondary btn */
    secBtn:       isDark
      ? 'border-white/10 hover:border-white/20 hover:bg-white/5 text-white/70 hover:text-white'
      : 'border-gray-200 hover:border-gray-400 hover:bg-gray-100 text-gray-600 hover:text-gray-900',
  };

  return (
    <div
      className={`min-h-screen transition-colors duration-500 ${t.bg} ${t.text}`}
      style={{ fontFamily: 'var(--font-sora, Sora, sans-serif)' }}
    >
      {/* Noise texture */}
      <div
        className={`fixed inset-0 pointer-events-none z-0 ${isDark ? 'opacity-[0.025]' : 'opacity-[0.012]'}`}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundSize: '200px 200px',
        }}
      />

      {/* ── Nav ─────────────────────────────────────────────── */}
      <nav className={`fixed top-0 left-0 right-0 z-50 border-b backdrop-blur-xl transition-colors duration-300 ${t.navBorder} ${t.navBg}`}>
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className={`text-lg font-semibold tracking-tight ${t.text}`}>
            Verus<span className="text-[#8B5CF6]">.</span>AI
          </span>

          {/* Desktop nav */}
          <div className={`hidden md:flex items-center gap-8 text-sm ${t.navLinks} transition-colors`}>
            <a href="#problema" className="transition-colors">Problema</a>
            <a href="#plataforma" className="transition-colors">Plataforma</a>
            <a href="#fluxos" className="transition-colors">Workflows</a>
            <a href="#ia" className="transition-colors">IA</a>
            <a href="#seguranca" className="transition-colors">Segurança</a>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className={`hidden sm:block text-sm transition-colors px-4 py-2 ${t.navEnter}`}
            >
              Entrar
            </Link>
            <a
              href={SCHEDULE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:block text-sm font-medium px-4 py-2 rounded-lg bg-[#7030A0] hover:bg-[#5B2EE0] transition-colors text-white"
            >
              Solicitar demo
            </a>
            {/* Theme toggle */}
            {mounted && (
              <button
                onClick={toggle}
                className={`p-2 rounded-lg transition-colors ${
                  isDark
                    ? 'text-white/50 hover:text-white hover:bg-white/8'
                    : 'text-gray-400 hover:text-gray-700 hover:bg-gray-100'
                }`}
                aria-label={isDark ? 'Modo claro' : 'Modo escuro'}
              >
                {isDark ? <Sun size={17} /> : <Moon size={17} />}
              </button>
            )}
            {/* Hamburger mobile */}
            <button
              className={`md:hidden p-2 transition-colors ${isDark ? 'text-white/60 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'}
              aria-expanded={menuOpen}
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {menuOpen && (
          <div className={`md:hidden border-t backdrop-blur-xl transition-colors ${t.mobileDivider} ${t.mobileBg}`}>
            <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col gap-1">
              {[
                { href: '#problema', label: 'Problema' },
                { href: '#plataforma', label: 'Plataforma' },
                { href: '#fluxos', label: 'Workflows' },
                { href: '#ia', label: 'IA' },
                { href: '#seguranca', label: 'Segurança' },
              ].map(item => (
                <a
                  key={item.href}
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className={`py-3 px-2 text-sm border-b last:border-0 transition-colors ${t.mobileItem}`}
                >
                  {item.label}
                </a>
              ))}
              <div className="pt-3 flex flex-col gap-2">
                <Link
                  href="/login"
                  onClick={() => setMenuOpen(false)}
                  className={`py-2.5 text-sm text-center border rounded-lg transition-colors ${t.mobileLogin}`}
                >
                  Entrar
                </Link>
                <a
                  href={SCHEDULE_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setMenuOpen(false)}
                  className="py-2.5 text-sm text-center font-medium rounded-lg bg-[#7030A0] hover:bg-[#5B2EE0] transition-colors text-white"
                >
                  Solicitar demo
                </a>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <div className="relative pt-32 pb-24 px-6 overflow-hidden">
        {/* Glow */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] pointer-events-none"
          style={{
            background: `radial-gradient(ellipse at center, rgba(112,48,160,${isDark ? '0.18' : '0.10'}) 0%, transparent 70%)`,
          }}
        />

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#7030A0]/30 bg-[#7030A0]/10 text-xs text-[#C084FC] font-medium mb-8">
            <Zap size={11} />
            Plataforma operacional para procuradorias
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight tracking-tight mb-6">
            Centro de operações{' '}
            <br className="hidden sm:block" />
            para{' '}
            <span className="text-[#C084FC]">procuradorias</span>
          </h1>

          <p className={`text-lg max-w-2xl mx-auto leading-relaxed mb-10 ${t.muted}`}>
            Processos judiciais e administrativos, fluxos BPMN por papel,
            geração de peças com IA e peticionamento — em uma plataforma construída
            para a realidade do setor público.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center w-full sm:w-auto">
            <a
              href={SCHEDULE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-center gap-2 w-full sm:w-auto px-6 py-3 rounded-lg bg-[#7030A0] hover:bg-[#5B2EE0] transition-all font-medium text-sm text-white"
              style={{ boxShadow: '0 0 24px rgba(112,48,160,0.35)' }}
            >
              Solicitar demonstração
              <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </a>
            <Link
              href="/login"
              className={`flex items-center justify-center gap-2 w-full sm:w-auto px-6 py-3 rounded-lg border transition-all font-medium text-sm ${t.secBtn}`}
            >
              Já tenho acesso
            </Link>
          </div>

          {/* Scroll indicator */}
          <div className="mt-16 flex justify-center scroll-nudge">
            <ChevronDown size={20} className={t.faint} />
          </div>
        </div>
      </div>

      {/* ── Problema ─────────────────────────────────────────── */}
      <Section id="problema" className={`py-24 px-6 border-t ${t.divider}`}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono text-[#8B5CF6] uppercase tracking-widest mb-4">O problema</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              Procuradorias operam com ferramentas{' '}
              <span className={t.faint}>que não foram feitas para elas</span>
            </h2>
            <p className={`max-w-xl mx-auto ${t.muted}`}>
              A gestão jurídica do setor público tem desafios únicos que escritórios privados
              não têm. As plataformas do mercado ignoram isso.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {PROBLEMS.map((p, i) => (
              <div
                key={i}
                className={`p-6 rounded-xl border transition-all ${t.card} ${t.cardHover}`}
              >
                <div className="flex items-start gap-4">
                  <div className={`shrink-0 w-9 h-9 rounded-lg flex items-center justify-center ${t.iconBg}`}>
                    <p.icon size={17} className="text-[#8B5CF6]" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm mb-1.5">{p.title}</h3>
                    <p className={`text-sm leading-relaxed ${t.muted}`}>{p.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Plataforma ───────────────────────────────────────── */}
      <Section id="plataforma" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono text-[#8B5CF6] uppercase tracking-widest mb-4">A plataforma</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              Tudo que uma procuradoria precisa,{' '}
              <br className="hidden sm:block" />
              integrado e inteligente
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f, i) => (
              <div
                key={i}
                className={`p-6 rounded-xl border transition-all group ${t.card} ${t.cardHover}`}
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-4 transition-all group-hover:scale-105"
                  style={{ background: `${f.color}22`, border: `1px solid ${f.color}33` }}
                >
                  <f.icon size={18} style={{ color: f.color }} />
                </div>
                <h3 className="font-semibold text-sm mb-2">{f.title}</h3>
                <p className={`text-sm leading-relaxed ${t.muted}`}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Workflows ────────────────────────────────────────── */}
      <Section id="fluxos" className={`py-24 px-6 border-t ${t.divider}`}>
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6 md:gap-16 items-center">
            <div>
              <p className="text-xs font-mono text-[#8B5CF6] uppercase tracking-widest mb-4">Workflows BPMN</p>
              <h2 className="text-3xl font-bold tracking-tight mb-6">
                O fluxo real da procuradoria,{' '}
                <span className="text-[#8B5CF6]">modelado e executável</span>
              </h2>
              <p className={`leading-relaxed mb-8 ${t.muted}`}>
                Mapeie os fluxos judiciais e administrativos com swim lanes por papel.
                Cada tarefa é atribuída automaticamente ao papel correto.
                Gateways controlam redistribuições, avocações e peticionamentos.
              </p>
              <ul className="space-y-3">
                {[
                  'Templates pré-carregados dos fluxos judiciais da PGM',
                  'Editor visual drag-and-drop sem código',
                  'Versionamento de fluxos com publicação controlada',
                  'Histórico imutável de execução por processo',
                ].map((item, i) => (
                  <li key={i} className={`flex items-start gap-3 text-sm ${t.muted}`}>
                    <CheckCircle2 size={15} className="text-[#8B5CF6] mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Flow visualization */}
            <div className={`rounded-2xl border p-6 ${t.flowBorder}`}>
              <p className={`text-xs font-mono mb-5 ${t.flowCaption}`}>
                Fluxograma Judicial — 1º Grau (exemplo)
              </p>
              <div className="relative pl-5">
                {/* Linha vertical conectora */}
                <div
                  className={`absolute left-[6px] top-[14px] w-px ${t.flowLine}`}
                  style={{ bottom: '28px' }}
                />
                <div className="space-y-2">
                  {FLOW_STEPS.map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div
                        className="relative z-10 shrink-0 w-3 h-3 rounded-full"
                        style={{
                          background: step.color,
                          boxShadow: `0 0 6px ${step.color}80`,
                          flexShrink: 0,
                        }}
                      />
                      <div className={`flex-1 p-3 rounded-lg border ${t.cardInner}`}>
                        <p className={`text-xs mb-0.5 ${t.flowRole}`}>{step.role}</p>
                        <p className="text-sm font-medium">{step.action}</p>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center gap-3 pt-1">
                    <div
                      className="relative z-10 shrink-0 w-3 h-3 rounded-full"
                      style={{ background: '#34D399', boxShadow: '0 0 6px rgba(52,211,153,0.5)' }}
                    />
                    <p className={`text-xs font-mono ${t.flowCaption}`}>Processo arquivado</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ── IA ───────────────────────────────────────────────── */}
      <Section id="ia" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-xs font-mono text-[#8B5CF6] uppercase tracking-widest mb-4">Inteligência artificial</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              IA que entende o contexto jurídico{' '}
              <span className={t.faint}>do setor público</span>
            </h2>
            <p className={`max-w-xl mx-auto ${t.muted}`}>
              O assistente de IA conhece o fluxo, o papel do usuário e o histórico do processo.
              Não é um chatbot genérico — é um copilot jurídico especializado.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4 mb-8">
            {[
              {
                title: 'Geração de Minutas',
                desc: 'Elabora minutas de despachos e petições com base no processo, adaptadas ao órgão e ao fluxo atual.',
                tag: 'assessor_gerencial / procurador',
              },
              {
                title: 'Resumo de Processo',
                desc: 'Condensa o histórico de movimentações, prazos e documentos em um briefing executivo para o gerente ou PG.',
                tag: 'gerente / procurador_geral',
              },
              {
                title: 'Análise de Prazos',
                desc: 'Monitora prazos judiciais ativos, alerta proativamente e sugere providências antes da perda do prazo.',
                tag: 'todos os papéis',
              },
            ].map((item, i) => (
              <div
                key={i}
                className={`p-6 rounded-xl border transition-all ${t.iaCard}`}
              >
                <h3 className="font-semibold text-sm mb-2">{item.title}</h3>
                <p className={`text-sm leading-relaxed mb-4 ${t.iaBody}`}>{item.desc}</p>
                <span
                  className="text-[10px] font-mono px-2 py-0.5 rounded border"
                  style={{
                    color: t.iaTagColor,
                    borderColor: t.iaTagBorder,
                    background: t.iaTagBg,
                  }}
                >
                  {item.tag}
                </span>
              </div>
            ))}
          </div>

          <div className={`rounded-xl border p-6 ${t.iaPanel}`}>
            <div className="flex items-start gap-3">
              <div className="shrink-0 w-8 h-8 rounded-lg bg-[#5B2EE0]/20 flex items-center justify-center">
                <Brain size={15} className="text-[#8B5CF6]" />
              </div>
              <div>
                <p className={`text-xs font-mono mb-1 ${t.iaCaption}`}>Providers de IA</p>
                <p className={`text-sm ${t.muted}`}>
                  IBM WatsonX como modelo primário de IA.
                  Dados nunca são usados para treino. Conformidade LGPD garantida por design.
                </p>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* ── Segurança ────────────────────────────────────────── */}
      <Section id="seguranca" className={`py-24 px-6 border-t ${t.divider}`}>
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6 md:gap-16 items-center">
            <div className="order-2 md:order-1">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { icon: Lock, label: 'JWT 15min', sub: 'Access tokens de curta duração' },
                  { icon: ShieldCheck, label: 'Isolamento por órgão', sub: 'Zero dados entre órgãos' },
                  { icon: Database, label: 'Auditoria completa', sub: 'Log imutável de todas as ações' },
                  { icon: Users, label: 'RBAC por papel', sub: 'Controle granular de acesso' },
                ].map((item, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border ${t.card}`}
                  >
                    <item.icon size={18} className="text-[#8B5CF6] mb-3" />
                    <p className="text-sm font-medium mb-1">{item.label}</p>
                    <p className={`text-xs ${t.faint}`}>{item.sub}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="order-1 md:order-2">
              <p className="text-xs font-mono text-[#8B5CF6] uppercase tracking-widest mb-4">Segurança</p>
              <h2 className="text-3xl font-bold tracking-tight mb-6">
                Construída para dados{' '}
                <span className="text-[#8B5CF6]">jurídicos sensíveis</span>
              </h2>
              <p className={`leading-relaxed mb-6 ${t.muted}`}>
                Dados de processos públicos exigem rigor. A plataforma implementa isolamento
                por órgão em todos os querysets, controle de acesso por papel baseado nos
                fluxos BPMN e auditoria de cada ação.
              </p>
              <ul className="space-y-3">
                {[
                  'LGPD nativo — mascaramento de PII em logs e prompts de IA',
                  'Dados de cada procuradoria completamente isolados',
                  'Revogação de tokens no logout',
                  'Rate limiting por usuário e por endpoint sensível',
                ].map((item, i) => (
                  <li key={i} className={`flex items-start gap-3 text-sm ${t.muted}`}>
                    <CheckCircle2 size={14} className="text-[#8B5CF6] mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </Section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <Section id="cta" className="py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <div
            className={`rounded-2xl border p-12 relative overflow-hidden ${t.ctaBorder}`}
            style={{ background: t.ctaBg }}
          >
            <div
              className="absolute inset-0 pointer-events-none"
              style={{ background: t.ctaInner }}
            />
            <h2 className="text-3xl font-bold tracking-tight mb-4 relative">
              Leve sua procuradoria para o próximo nível
            </h2>
            <p className={`leading-relaxed mb-8 relative ${t.ctaBody}`}>
              Agende uma demonstração personalizada. Mostraremos como a plataforma
              se adapta ao fluxo real da sua procuradoria.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center relative">
              <a
                href={SCHEDULE_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-[#7030A0] hover:bg-[#5B2EE0] transition-all font-medium text-sm text-white"
                style={{ boxShadow: '0 0 32px rgba(112,48,160,0.35)' }}
              >
                Agendar demonstração
                <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
              </a>
              <Link
                href="/login"
                className={`flex items-center justify-center gap-2 px-6 py-3 rounded-lg border transition-all font-medium text-sm ${t.secBtn}`}
              >
                Já tenho acesso
              </Link>
            </div>
          </div>
        </div>
      </Section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className={`border-t py-12 px-6 ${t.divider}`}>
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm font-semibold">
            Verus<span className="text-[#8B5CF6]">.</span>AI
          </span>
          <p className={`text-xs ${t.footerCaption}`}>
            Plataforma operacional para procuradorias. Powered by Bravonix.
          </p>
          <div className={`flex items-center gap-6 text-xs ${t.footerLinks}`}>
            <Link href="/privacidade" className="transition-colors">Privacidade</Link>
            <Link href="/cookies" className="transition-colors">Cookies</Link>
            <Link href="/login" className="transition-colors">Entrar</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
