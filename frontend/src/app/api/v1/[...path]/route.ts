/**
 * Proxy Runtime para o Backend Django — App Router Route Handler
 *
 * Diferença crítica em relação aos rewrites do next.config.js:
 *   - rewrites: compilados em BUILD TIME → BACKEND_URL deve estar correto no momento do build
 *   - Route Handler: executado em RUNTIME → lê process.env.BACKEND_URL do ambiente do container
 *
 * Benefícios:
 *   - Suporta SSE/streaming (ReadableStream passthrough nativo)
 *   - Imune a variáveis de ambiente incorretas no build
 *   - Permite adicionar headers de segurança e logging
 *   - Controle total sobre request/response
 */

import { type NextRequest, NextResponse } from 'next/server'

// Lida em runtime, não em build time
const BACKEND_URL = process.env.BACKEND_URL || 'http://verus-backend:8000'

// Headers hop-by-hop que nunca devem ser repassados
const HOP_BY_HOP = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailers',
  'transfer-encoding',
  'upgrade',
])

/**
 * Constrói os headers a serem encaminhados ao backend.
 * Mantém Authorization, Content-Type, Cookie e headers customizados.
 * Remove hop-by-hop e headers que o Next.js controla (Host).
 */
function buildForwardHeaders(request: NextRequest, clientIp: string): Headers {
  const headers = new Headers()

  for (const [key, value] of request.headers.entries()) {
    const lower = key.toLowerCase()
    if (HOP_BY_HOP.has(lower)) continue
    headers.set(key, value)
  }

  // Encaminha o Host original do browser (ex: verus.ai).
  // Seguro porque: (1) redirect:'manual' impede loops de redirect internos,
  // (2) trailing slash é sempre adicionado eliminando APPEND_SLASH redirects,
  // (3) SECURE_SSL_REDIRECT=False no Django.
  // Usar host interno causava 400 Bad Request porque ALLOWED_HOSTS em produção
  // só contém o domínio público.
  const originalHost =
    request.headers.get('x-forwarded-host') ||
    request.headers.get('host') ||
    new URL(BACKEND_URL).host
  headers.set('host', originalHost)

  // Informa ao Django o IP real do cliente (para logging e rate-limiting)
  headers.set('X-Forwarded-For', clientIp)
  headers.set('X-Real-IP', clientIp)
  headers.set('X-Forwarded-Proto', 'https')

  return headers
}

/**
 * Headers de segurança adicionados a toda resposta proxy.
 */
function addSecurityHeaders(responseHeaders: Headers): Headers {
  responseHeaders.set('X-Content-Type-Options', 'nosniff')
  responseHeaders.set('X-Frame-Options', 'DENY')
  responseHeaders.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  // Impede que o browser cache respostas de API (previne redirects stale de 301/308)
  responseHeaders.set('Cache-Control', 'no-store, no-cache, must-revalidate')
  // Remove headers que expõem informações do backend
  responseHeaders.delete('X-Powered-By')
  responseHeaders.delete('Server')
  return responseHeaders
}

/**
 * Proxy genérico — encaminha a request ao Django e retorna a resposta.
 * Suporta SSE (text/event-stream) e download de arquivos via ReadableStream.
 */
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params
  const { search } = request.nextUrl

  // SEMPRE adiciona trailing slash ao encaminhar para Django.
  // Motivo: Next.js faz redirect 308 para REMOVER trailing slash ANTES
  // do Route Handler rodar (comportamento padrão com trailingSlash:false).
  // Então pathname.endsWith('/') é sempre false aqui — e Django/DRF
  // exige trailing slash nos URL patterns (DefaultRouter gera /users/me/).
  // Sem o slash, Django retorna 400 Bad Request.
  const targetUrl = `${BACKEND_URL}/api/v1/${path.join('/')}/${search}`

  // IP do cliente (Traefik injeta X-Forwarded-For ou X-Real-IP)
  const clientIp =
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    request.headers.get('x-real-ip') ||
    '127.0.0.1'

  const forwardHeaders = buildForwardHeaders(request, clientIp)

  // Detecta se a request provavelmente será SSE (streaming longo).
  // Endpoints de simulação SSE podem durar vários minutos (múltiplas chamadas LLM).
  const isSSE = targetUrl.includes('/jury/start/') || targetUrl.includes('/judge/start/') || targetUrl.includes('/stf/start/') || targetUrl.includes('/acordao/start/') || targetUrl.includes('/stj/start/') || targetUrl.includes('/jec/start/') || targetUrl.includes('/jecrim/start/') || targetUrl.includes('/eleitoral/start/') || targetUrl.includes('/tre/start/') || targetUrl.includes('/tse/start/') || targetUrl.includes('/trabalho/start/') || targetUrl.includes('/trt/start/') || targetUrl.includes('/tst/start/') || targetUrl.includes('/turma-recursal/start/') || targetUrl.includes('/militar/start/') || targetUrl.includes('/stm/start/')
  const timeoutMs = isSSE ? 600_000 : 29_000 // 10min para SSE, 29s para o resto

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  const init: RequestInit = {
    method: request.method,
    headers: forwardHeaders,
    signal: controller.signal,
    // CRÍTICO: 'manual' impede o fetch de seguir redirects automaticamente.
    // Se Django retornar 301/302 (APPEND_SLASH, SECURE_SSL_REDIRECT, view redirect),
    // o Route Handler repassa o status+Location ao browser em vez de seguir o redirect
    // internamente — o que causaria loop infinito quando o Location aponta para o
    // domínio público (Traefik → Next.js → Route Handler → Django → redirect → loop).
    redirect: 'manual',
  }

  // Encaminha body apenas para métodos que o possuem
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    // @ts-ignore — duplex é necessário para streaming de request body (Node.js 18+)
    init.duplex = 'half'
    init.body = request.body
  }

  let backendResponse: Response
  try {
    backendResponse = await fetch(targetUrl, init)
    clearTimeout(timeoutId)
  } catch (err: any) {
    clearTimeout(timeoutId)
    const isTimeout = err?.name === 'AbortError'
    console.error('[proxy] Erro ao contatar backend:', targetUrl, isTimeout ? '(timeout)' : err)
    return NextResponse.json(
      { detail: isTimeout ? 'Backend demorou demais para responder. Tente novamente.' : 'Backend temporariamente indisponível. Tente novamente.' },
      { status: 502 },
    )
  }

  // Constrói headers de resposta (remove hop-by-hop)
  const responseHeaders = new Headers()
  for (const [key, value] of backendResponse.headers.entries()) {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      responseHeaders.set(key, value)
    }
  }
  addSecurityHeaders(responseHeaders)

  // Para SSE, preserva os headers do backend (Cache-Control: no-cache, X-Accel-Buffering: no)
  // e garante que proxies intermediários não buffurizem o stream.
  const contentType = backendResponse.headers.get('content-type') || ''
  if (contentType.includes('text/event-stream')) {
    responseHeaders.set('Cache-Control', 'no-cache')
    responseHeaders.set('X-Accel-Buffering', 'no')
    responseHeaders.set('Connection', 'keep-alive')
  }

  // Retorna com ReadableStream passthrough — preserva SSE e downloads
  return new Response(backendResponse.body, {
    status: backendResponse.status,
    statusText: backendResponse.statusText,
    headers: responseHeaders,
  })
}

export const GET = proxy
export const POST = proxy
export const PUT = proxy
export const PATCH = proxy
export const DELETE = proxy
export const OPTIONS = proxy
export const HEAD = proxy

// Força Node.js runtime (não Edge) para ter acesso a process.env em runtime
// e suporte completo a streams
export const runtime = 'nodejs'

// Desabilita cache estático — respostas da API nunca devem ser cacheadas pelo Next.js
export const dynamic = 'force-dynamic'
