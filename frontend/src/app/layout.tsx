import type { Metadata, Viewport } from "next";
import { Sora, JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { QueryProvider } from "@/components/providers/query-provider";
import { BrandProvider } from "@/components/providers/brand-provider";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { ThemeProvider } from "next-themes";

/* ── Fontes Bravonix ──────────────────────────────────────── */
const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
  weight: ["300", "400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

/* ── Metadados ────────────────────────────────────────────── */
export const metadata: Metadata = {
  title: "Verus.AI - Agente de Justiça",
  description:
    "Assistente de procuradoria com IA para geração de peças processuais e pesquisa jurisprudencial.",
  // O BrandProvider sobrescreve o favicon dinamicamente quando carrega brand settings.
  // Este fallback garante que /favicon.ico não retorne 404 antes do JS carregar.
  icons: {
    icon: '/favicon.png',
    apple: '/favicon.png',
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      suppressHydrationWarning
      className={`${sora.variable} ${jetbrainsMono.variable}`}
    >
      <body className="font-sans antialiased" suppressHydrationWarning>
        {/*
          defaultTheme="light" - modo claro como padrao.
          enableSystem={false} - ignora preferencia do sistema;
          o usuario controla via toggle no header.
        */}
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange={false}
          storageKey="verus-theme"
        >
          <QueryProvider>
            <BrandProvider>
              {children}
            </BrandProvider>
            <Toaster />
            <SonnerToaster position="top-right" richColors />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
