/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Para Docker multi-stage build
  outputFileTracingRoot: require('path').join(__dirname),
  // Turbopack root: explicitamos o diretório raiz do projeto
  turbopack: {
    root: __dirname,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8001',
        pathname: '/media/**',
      },
      {
        protocol: 'http',
        hostname: 'backend',
        port: '8000',
        pathname: '/media/**',
      },
      {
        protocol: 'https',
        hostname: 'verus.ai',
        pathname: '/media/**',
      },
    ],
  },
  // SEGURANÇA: Headers de proteção
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ]
  },
  // PROXY: /api/v1/* é tratado pelo Route Handler em src/app/api/v1/[...path]/route.ts
  // que roda em Node.js runtime e lê BACKEND_URL em runtime (não build-time).
  // Rewrites de next.config.js foram removidos porque: (1) são compilados em build-time
  // tornando-os vulneráveis a BACKEND_URL incorreto no build; (2) têm precedência sobre
  // Route Handlers, impedindo o proxy runtime de funcionar.
  //
  // /api/schema/* ainda é rewritado aqui pois não tem Route Handler dedicado.
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/schema/:path*',
        destination: `${backendUrl}/api/schema/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
