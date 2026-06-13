'use client';

import { useState } from 'react';
import { useClientPortalAuth } from '@/hooks/use-client-portal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Scale, Loader2, Eye, EyeOff, AlertCircle } from 'lucide-react';

export default function ClientLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, loginLoading, error } = useClientPortalAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-background px-4 py-8">

      {/* Decorative rings */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 flex items-center justify-center">
        {[340, 480, 620].map((size, i) => (
          <span
            key={size}
            className="absolute rounded-full border border-primary/10"
            style={{ width: size, height: size, opacity: 1 - i * 0.25 }}
          />
        ))}
      </div>

      {/* Login card */}
      <div className="relative z-10 w-full max-w-sm">

        {/* Branding */}
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary shadow-md">
            <Scale className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
              Portal de Acompanhamento
            </h1>
            <p className="mt-1 text-sm text-muted-foreground font-mono tracking-wide">
              Verus.AI
            </p>
          </div>
        </div>

        {/* Form */}
        <div className="rounded-2xl border bg-card p-5 sm:p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">
                E-mail
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loginLoading}
                autoComplete="email"
                className="h-11"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-sm font-medium">
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
                  disabled={loginLoading}
                  autoComplete="current-password"
                  className="h-11 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center justify-center h-11 w-11 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/8 px-3 py-2.5 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-12 sm:h-11 text-base sm:text-sm font-semibold"
              disabled={loginLoading || !email || !password}
            >
              {loginLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Entrar no Portal'
              )}
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-[11px] text-muted-foreground leading-relaxed px-2">
          Acesso exclusivo para clientes com portal ativado pela procuradoria.
        </p>
      </div>
    </div>
  );
}
