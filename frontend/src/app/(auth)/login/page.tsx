'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { resetRedirectFlag } from '@/lib/api';
import { useBrandSettings } from '@/hooks/use-brand-settings';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Scale,
  Loader2,
  Eye,
  EyeOff,
  AlertCircle,
  Lock,
  Shield,
  FileText,
  Brain,
  Gavel,
  Briefcase,
  Sparkles,
  ChevronRight,
  Users,
  Zap,
  BarChart3,
  Bot,
  Sun,
  Moon,
} from 'lucide-react';
import Image from 'next/image';

// ─── Theme toggle for login page ───
function useLoginTheme() {
  const [isDark, setIsDark] = useState(false);
  useEffect(() => {
    // Default: light mode
    const saved = localStorage.getItem('verus-login-theme');
    setIsDark(saved === 'dark');
  }, []);
  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem('verus-login-theme', next ? 'dark' : 'light');
  };
  return { isDark, toggle };
}

// ─── Animated Grid Background ───
function AnimatedBackground({ isDark }: { isDark: boolean }) {
  const base = isDark ? 'rgba(139,92,246,' : 'rgba(112,48,160,';
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Gradient orbs */}
      <div
        className="absolute -top-[30%] -right-[15%] w-[60%] h-[60%] rounded-full"
        style={{
          background: `radial-gradient(circle, ${base}${isDark ? '0.08' : '0.06'}) 0%, transparent 70%)`,
          animation: 'float-slow 20s ease-in-out infinite',
        }}
      />
      <div
        className="absolute -bottom-[20%] -left-[10%] w-[50%] h-[50%] rounded-full"
        style={{
          background: `radial-gradient(circle, ${base}${isDark ? '0.06' : '0.04'}) 0%, transparent 70%)`,
          animation: 'float-slow 25s ease-in-out infinite reverse',
        }}
      />
      {/* Dot grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `radial-gradient(${isDark ? 'rgba(139,92,246,0.15)' : 'rgba(112,48,160,0.08)'} 1px, transparent 1px)`,
          backgroundSize: '32px 32px',
        }}
      />
      {/* Accent line */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-full"
        style={{
          background: `linear-gradient(to bottom, transparent 0%, ${base}${isDark ? '0.12' : '0.06'}) 30%, ${base}${isDark ? '0.12' : '0.06'}) 70%, transparent 100%)`,
        }}
      />
    </div>
  );
}

// ─── Feature Pill ───
function FeaturePill({ icon: Icon, text, isDark }: { icon: any; text: string; isDark: boolean }) {
  return (
    <div className={`
      flex items-center gap-2.5 px-4 py-2.5 rounded-2xl border transition-all duration-300
      ${isDark
        ? 'border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06]'
        : 'border-gray-200 bg-white/80 hover:bg-white shadow-sm hover:shadow-md'}
    `}>
      <div className={`
        w-8 h-8 rounded-xl flex items-center justify-center
        ${isDark ? 'bg-purple-500/10' : 'bg-purple-50'}
      `}>
        <Icon className={`w-4 h-4 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
      </div>
      <span className={`text-sm font-medium ${isDark ? 'text-white/80' : 'text-gray-700'}`}>
        {text}
      </span>
    </div>
  );
}

// ─── Main Login Page ───
export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [clientEmail, setClientEmail] = useState('');
  const [clientPassword, setClientPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showClientPassword, setShowClientPassword] = useState(false);
  const [activeTab, setActiveTab] = useState('advogado');
  const [mounted, setMounted] = useState(false);
  const { login, loading, error, isAuthenticated } = useAuth();
  const { brandSettings } = useBrandSettings();
  const { isDark, toggle } = useLoginTheme();
  const router = useRouter();

  // Reset redirect flag when landing on login (e.g. after session expiry redirect)
  useEffect(() => {
    resetRedirectFlag();
  }, []);

  // Redirect already-authenticated users to dashboard
  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, loading, router]);

  useEffect(() => setMounted(true), []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await login({ username, password }); } catch { /* hook handles */ }
  };

  const handleClientSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await login({ username: clientEmail, password: clientPassword }); } catch { /* hook handles */ }
  };

  if (!mounted) return null;

  return (
    <div className={`relative min-h-screen flex flex-col lg:flex-row overflow-hidden transition-colors duration-500 ${isDark ? 'bg-[#09090B]' : 'bg-[#FAFAFA]'}`}>
      <AnimatedBackground isDark={isDark} />

      {/* Theme Toggle */}
      <button
        onClick={toggle}
        className={`
          fixed top-5 right-5 z-50 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
          ${isDark ? 'bg-white/10 hover:bg-white/15 text-white/60' : 'bg-gray-100 hover:bg-gray-200 text-gray-500'}
        `}
        aria-label="Alternar tema"
      >
        {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </button>

      {/* ── LEFT — Brand & Vision (60%) ── */}
      <div className="relative z-10 flex-1 lg:w-[60%] flex flex-col justify-center px-6 sm:px-10 lg:px-16 xl:px-24 py-12 lg:py-16 order-2 lg:order-1">

        {/* Logo */}
        <div className="mb-10">
          <div className="flex items-center gap-3">
            <Image
              src="/logo.png"
              alt="Verus.AI"
              width={44}
              height={44}
              className="h-10 w-10 object-contain shrink-0"
              unoptimized
            />
            <div>
              <span className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Verus<span className="text-[#7030A0]">.AI</span>
              </span>
              <span className={`block text-[10px] font-medium tracking-widest uppercase ${isDark ? 'text-white/40' : 'text-gray-400'}`}>
                by Bravonix
              </span>
            </div>
          </div>
        </div>

        {/* Tagline */}
        <p className={`text-[11px] font-semibold tracking-[0.2em] uppercase mb-5 ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>
          Inteligência Artificial para Procuradorias Municipais
        </p>

        {/* Hero */}
        <h1 className={`text-2xl sm:text-3xl lg:text-4xl xl:text-[3.5rem] font-extrabold tracking-[-0.03em] leading-[1.05] mb-5 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Sua procuradoria,{' '}
          <span className="text-[#7030A0]">
            mais eficaz.
          </span>
        </h1>

        <p className={`text-base sm:text-lg max-w-xl leading-relaxed mb-10 ${isDark ? 'text-white/55' : 'text-gray-500'}`}>
          Verus.AI centraliza o contencioso, automatiza minutas e pareceres, e coloca
          a inteligência artificial a serviço de quem defende o interesse público municipal —
          com rastreabilidade, segurança e conformidade LGPD.
        </p>

        {/* Feature Pills */}
        <div className="flex flex-wrap gap-3 mb-10">
          <FeaturePill icon={Brain} text="IA Generativa Jurídica" isDark={isDark} />
          <FeaturePill icon={BarChart3} text="Gestão da Dívida Ativa" isDark={isDark} />
          <FeaturePill icon={FileText} text="Automação de Minutas" isDark={isDark} />
          <FeaturePill icon={Shield} text="Conformidade LGPD" isDark={isDark} />
        </div>

        {/* Vision Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          {[
            {
              icon: Zap,
              title: 'Eficiência',
              desc: 'Automatize minutas, pareceres e despachos — foque no que importa.',
            },
            {
              icon: Bot,
              title: 'Confiabilidade',
              desc: 'IA com rastreabilidade total, treinada no direito público brasileiro.',
            },
            {
              icon: Sparkles,
              title: 'Controle',
              desc: 'Contencioso, dívida ativa e consultivo reunidos em um só lugar.',
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className={`
                group rounded-2xl border p-5 transition-all duration-300
                ${isDark
                  ? 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-purple-500/20'
                  : 'border-gray-100 bg-white/60 hover:bg-white hover:shadow-lg hover:shadow-purple-500/5 hover:border-purple-200'}
              `}
            >
              <div className={`
                w-10 h-10 rounded-xl flex items-center justify-center mb-3 transition-colors duration-300
                ${isDark ? 'bg-purple-500/10 group-hover:bg-purple-500/15' : 'bg-purple-50 group-hover:bg-purple-100'}
              `}>
                <Icon className={`w-5 h-5 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
              </div>
              <h3 className={`text-sm font-bold mb-1.5 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-white/40' : 'text-gray-500'}`}>{desc}</p>
            </div>
          ))}
        </div>

        {/* IBM Infrastructure Badge */}
        <div className={`flex flex-wrap items-center gap-4 mb-4 ${isDark ? 'text-white/30' : 'text-gray-400'}`}>
          <div className="flex items-center gap-2 text-[11px] font-medium tracking-wide">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Plataforma ativa e em constante evolução
          </div>
        </div>
        <div className={`flex items-center gap-2 text-[10px] font-medium tracking-wide uppercase ${isDark ? 'text-white/20' : 'text-gray-400'}`}>
          <span>Infraestrutura</span>
          <span className={`font-bold ${isDark ? 'text-blue-400/60' : 'text-blue-600/60'}`}>IBM watsonx</span>
          <span className={`w-px h-3 ${isDark ? 'bg-white/10' : 'bg-gray-300'}`} />
          <span className={`font-bold ${isDark ? 'text-blue-400/60' : 'text-blue-600/60'}`}>IBM Orchestrate</span>
        </div>
      </div>

      {/* ── RIGHT — Login (40%) ── */}
      <div className="relative z-10 lg:w-[40%] flex items-center justify-center px-4 sm:px-8 py-8 lg:py-0 order-1 lg:order-2">
        <div className={`
          absolute inset-0 hidden lg:block
          ${isDark ? '' : 'bg-white/40 backdrop-blur-sm'}
        `} style={isDark ? {
          background: 'linear-gradient(135deg, rgba(9,9,11,0.5) 0%, rgba(42,14,74,0.1) 100%)',
          backdropFilter: 'blur(40px)',
        } : {}} />

        <div className="relative z-10 w-full max-w-sm lg:max-w-[400px]">
          {/* Card Header */}
          <div className="mb-6 text-center">
            <Image
              src="/logo.png"
              alt="Verus.AI"
              width={56}
              height={56}
              className="mx-auto h-14 w-14 object-contain mb-4"
              unoptimized
            />
            <h2 className={`text-xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {brandSettings?.system_name || 'Verus.AI'}
            </h2>
            <p className={`mt-1 text-sm ${isDark ? 'text-white/50' : 'text-gray-500'}`}>
              Acesse o sistema da procuradoria
            </p>
          </div>

          {/* Login Card */}
          <div className={`
            rounded-2xl border p-4 sm:p-6 lg:p-7 shadow-xl transition-colors duration-500
            ${isDark
              ? 'border-white/[0.08] bg-[#18181B]/80 backdrop-blur-xl shadow-black/40'
              : 'border-gray-200 bg-white shadow-gray-200/50'}
          `}>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className={`
                grid w-full grid-cols-2 mb-6 rounded-xl h-11
                ${isDark ? 'bg-white/[0.04] border border-white/[0.08]' : 'bg-gray-100 border border-gray-200'}
              `}>
                <TabsTrigger
                  value="advogado"
                  className={`
                    rounded-lg text-xs font-semibold transition-all duration-200
                    data-[state=active]:bg-[#7030A0] data-[state=active]:text-white data-[state=active]:shadow-sm
                    ${isDark ? 'text-white/50' : 'text-gray-500'}
                  `}
                >
                  <Briefcase className="w-3.5 h-3.5 mr-1.5" />
                  Assessor Jurídico
                </TabsTrigger>
                <TabsTrigger
                  value="cliente"
                  className={`
                    rounded-lg text-xs font-semibold transition-all duration-200
                    data-[state=active]:bg-[#7030A0] data-[state=active]:text-white data-[state=active]:shadow-sm
                    ${isDark ? 'text-white/50' : 'text-gray-500'}
                  `}
                >
                  <Users className="w-3.5 h-3.5 mr-1.5" />
                  Portal do Cidadão
                </TabsTrigger>
              </TabsList>

              {/* Assessor Login */}
              <TabsContent value="advogado" className="mt-0">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="username" className={`text-xs font-medium ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                      Usuário
                    </Label>
                    <Input
                      id="username"
                      type="text"
                      placeholder="Digite seu usuário"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      disabled={loading}
                      autoComplete="username"
                      className={`
                        h-11 rounded-xl transition-colors
                        ${isDark
                          ? 'bg-white/[0.04] border-white/[0.12] text-white placeholder:text-white/25 focus:border-purple-500 focus:ring-purple-500/20'
                          : 'bg-gray-50 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-500 focus:ring-purple-500/20 focus:bg-white'}
                      `}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="password" className={`text-xs font-medium ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                      Senha
                    </Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Digite sua senha"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                        autoComplete="current-password"
                        className={`
                          h-11 pr-10 rounded-xl transition-colors
                          ${isDark
                            ? 'bg-white/[0.04] border-white/[0.12] text-white placeholder:text-white/25 focus:border-purple-500 focus:ring-purple-500/20'
                            : 'bg-gray-50 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-500 focus:ring-purple-500/20 focus:bg-white'}
                        `}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className={`absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center h-9 w-9 transition-colors ${isDark ? 'text-white/40 hover:text-white/70' : 'text-gray-400 hover:text-gray-600'}`}
                        tabIndex={-1}
                        aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  {error && activeTab === 'advogado' && (
                    <div className="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-50 dark:bg-red-500/5 px-3 py-2.5 text-xs text-red-600 dark:text-red-400">
                      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full h-11 text-sm font-semibold bg-gradient-to-r from-[#7030A0] to-[#5B2EE0] hover:from-[#5B2EE0] hover:to-[#7030A0] text-white shadow-lg shadow-purple-500/20 rounded-xl border-0 transition-all duration-300"
                    disabled={loading || !username || !password}
                  >
                    {loading ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Entrando...</>
                    ) : (
                      <>Entrar <ChevronRight className="ml-1 h-4 w-4" /></>
                    )}
                  </Button>

                  <button
                    type="button"
                    className="w-full text-center text-xs text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 transition-colors mt-2 font-medium"
                  >
                    Esqueci minha senha
                  </button>
                </form>
              </TabsContent>

              {/* Portal do Cidadão */}
              <TabsContent value="cliente" className="mt-0">
                <form onSubmit={handleClientSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="clientEmail" className={`text-xs font-medium ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                      E-mail ou CPF
                    </Label>
                    <Input
                      id="clientEmail"
                      type="text"
                      placeholder="Digite seu e-mail ou CPF"
                      value={clientEmail}
                      onChange={(e) => setClientEmail(e.target.value)}
                      required
                      disabled={loading}
                      autoComplete="username"
                      className={`
                        h-11 rounded-xl transition-colors
                        ${isDark
                          ? 'bg-white/[0.04] border-white/[0.12] text-white placeholder:text-white/25 focus:border-purple-500'
                          : 'bg-gray-50 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-500 focus:bg-white'}
                      `}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="clientPassword" className={`text-xs font-medium ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                      Senha do Portal
                    </Label>
                    <div className="relative">
                      <Input
                        id="clientPassword"
                        type={showClientPassword ? 'text' : 'password'}
                        placeholder="Digite sua senha"
                        value={clientPassword}
                        onChange={(e) => setClientPassword(e.target.value)}
                        required
                        disabled={loading}
                        autoComplete="current-password"
                        className={`
                          h-11 pr-10 rounded-xl transition-colors
                          ${isDark
                            ? 'bg-white/[0.04] border-white/[0.12] text-white placeholder:text-white/25 focus:border-purple-500'
                            : 'bg-gray-50 border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-purple-500 focus:bg-white'}
                        `}
                      />
                      <button
                        type="button"
                        onClick={() => setShowClientPassword(!showClientPassword)}
                        className={`absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center h-9 w-9 transition-colors ${isDark ? 'text-white/40 hover:text-white/70' : 'text-gray-400 hover:text-gray-600'}`}
                        tabIndex={-1}
                        aria-label={showClientPassword ? 'Ocultar senha' : 'Mostrar senha'}
                      >
                        {showClientPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  {error && activeTab === 'cliente' && (
                    <div className="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-50 dark:bg-red-500/5 px-3 py-2.5 text-xs text-red-600 dark:text-red-400">
                      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                      <span>{error}</span>
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full h-11 text-sm font-semibold bg-gradient-to-r from-[#7030A0] to-[#5B2EE0] hover:from-[#5B2EE0] hover:to-[#7030A0] text-white shadow-lg shadow-purple-500/20 rounded-xl border-0 transition-all duration-300"
                    disabled={loading || !clientEmail || !clientPassword}
                  >
                    {loading ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Entrando...</>
                    ) : (
                      <>Acessar Portal <ChevronRight className="ml-1 h-4 w-4" /></>
                    )}
                  </Button>

                  <button
                    type="button"
                    className="w-full text-center text-xs text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 transition-colors mt-2 font-medium"
                  >
                    Esqueci minha senha
                  </button>
                </form>
              </TabsContent>
            </Tabs>
          </div>

          {/* Trust */}
          <div className="mt-5 flex items-center justify-center gap-5">
            <div className={`flex items-center gap-1.5 text-[10px] font-medium tracking-wide uppercase ${isDark ? 'text-white/30' : 'text-gray-400'}`}>
              <Lock className="w-3 h-3" /> Conexão segura
            </div>
            <div className={`w-px h-3 ${isDark ? 'bg-white/10' : 'bg-gray-300'}`} />
            <div className={`flex items-center gap-1.5 text-[10px] font-medium tracking-wide uppercase ${isDark ? 'text-white/30' : 'text-gray-400'}`}>
              <Shield className="w-3 h-3" /> Dados protegidos pela LGPD
            </div>
          </div>

          {/* Disclaimer */}
          <p className={`mt-4 text-center text-[10px] leading-relaxed px-2 ${isDark ? 'text-white/20' : 'text-gray-400'}`}>
            Verus.AI é uma plataforma de gestão jurídica com IA{' '}
            <strong className={`font-medium ${isDark ? 'text-white/30' : 'text-gray-500'}`}>para procuradorias municipais.</strong>
          </p>
        </div>
      </div>

      {/* Animations */}
      <style jsx global>{`
        @keyframes float-slow {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -25px) scale(1.03); }
          66% { transform: translate(-20px, 15px) scale(0.97); }
        }
        @media (prefers-reduced-motion: reduce) {
          * { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
        }
      `}</style>
    </div>
  );
}
