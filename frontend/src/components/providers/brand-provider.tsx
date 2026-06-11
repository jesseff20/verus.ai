"use client";

import { useEffect, useRef } from 'react';
import { useBrandSettings } from '@/hooks/use-brand-settings';

const DEFAULT_FAVICON = '/favicon.png';

/**
 * Provider que aplica configurações de marca dinamicamente:
 * - CSS Variables para cores
 * - Favicon dinâmico (R2 ou default local)
 * - Title da página
 *
 * IMPORTANTE: Nunca remove/cria elementos <link> no <head>.
 * Apenas ATUALIZA o href de links existentes (renderizados pelo Next.js via SSR).
 * Remover nós DOM que o React gerencia causa "Cannot read properties of null
 * (reading 'removeChild')" quando o reconciler tenta desmontar nós já removidos.
 */
export function BrandProvider({ children }: { children: React.ReactNode }) {
  const { brandSettings } = useBrandSettings();

  // Ref para guardar os valores já aplicados e evitar trabalho redundante
  const appliedRef = useRef<{
    primary: string;
    secondary: string;
    accent: string;
    favicon: string;
    title: string;
  } | null>(null);

  useEffect(() => {
    if (!brandSettings) return;

    const faviconUrl = brandSettings.favicon || DEFAULT_FAVICON;
    const titleSuffix = brandSettings.system_tagline
      ? ` - ${brandSettings.system_tagline}`
      : ' - Sistema de Gestão de Documentos';
    const fullTitle = brandSettings.system_name
      ? `${brandSettings.system_name}${titleSuffix}`
      : '';

    // Verificar se algo realmente mudou
    const prev = appliedRef.current;
    if (
      prev &&
      prev.primary === brandSettings.primary_color &&
      prev.secondary === brandSettings.secondary_color &&
      prev.accent === brandSettings.accent_color &&
      prev.favicon === faviconUrl &&
      prev.title === fullTitle
    ) {
      return; // Nada mudou, não fazer nada
    }

    // ── 1. Aplicar cores via CSS Variables no :root ──
    const root = document.documentElement;

    const hexToHSL = (hex: string) => {
      hex = hex.replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16) / 255;
      const g = parseInt(hex.substring(2, 4), 16) / 255;
      const b = parseInt(hex.substring(4, 6), 16) / 255;

      const max = Math.max(r, g, b);
      const min = Math.min(r, g, b);
      let h = 0;
      let s = 0;
      const l = (max + min) / 2;

      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

        switch (max) {
          case r:
            h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
            break;
          case g:
            h = ((b - r) / d + 2) / 6;
            break;
          case b:
            h = ((r - g) / d + 4) / 6;
            break;
        }
      }

      return `${Math.round(h * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
    };

    root.style.setProperty('--primary', hexToHSL(brandSettings.primary_color));
    root.style.setProperty('--primary-original', brandSettings.primary_color);
    root.style.setProperty('--secondary', hexToHSL(brandSettings.secondary_color));
    root.style.setProperty('--secondary-original', brandSettings.secondary_color);
    root.style.setProperty('--accent', hexToHSL(brandSettings.accent_color));
    root.style.setProperty('--accent-original', brandSettings.accent_color);

    // ── 2. Favicon dinâmico ──
    // NUNCA remover/criar links. Apenas atualizar href dos existentes.
    // Next.js renderiza <link rel="icon"> e <link rel="apple-touch-icon"> via
    // metadata em layout.tsx. Remover esses nós causa o erro removeChild(null)
    // porque o React reconciler ainda mantém referência a eles.
    const existingIcon = document.querySelector<HTMLLinkElement>("link[rel='icon']");
    if (existingIcon) {
      existingIcon.href = faviconUrl;
    } else {
      // Fallback: se por algum motivo não existe, criar um novo
      const link = document.createElement('link');
      link.rel = 'icon';
      link.href = faviconUrl;
      document.head.appendChild(link);
    }

    const existingApple = document.querySelector<HTMLLinkElement>("link[rel='apple-touch-icon']");
    if (existingApple) {
      existingApple.href = faviconUrl;
    } else {
      const appleLink = document.createElement('link');
      appleLink.rel = 'apple-touch-icon';
      appleLink.href = faviconUrl;
      document.head.appendChild(appleLink);
    }

    // ── 3. Atualizar o título da página ──
    if (fullTitle) {
      document.title = fullTitle;
    }

    // Guardar valores aplicados
    appliedRef.current = {
      primary: brandSettings.primary_color,
      secondary: brandSettings.secondary_color,
      accent: brandSettings.accent_color,
      favicon: faviconUrl,
      title: fullTitle,
    };
  }, [brandSettings]);

  // Sem cleanup: não removemos nenhum nó DOM, apenas atualizamos hrefs.
  // Os links pertencem ao Next.js/React e serão gerenciados por eles.

  return <>{children}</>;
}
