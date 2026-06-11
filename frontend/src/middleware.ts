import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Middleware Next.js — proteção de rotas de dashboard.
 *
 * Rotas /api/* são proxiadas para o backend Django via rewrites em next.config.js
 * e NÃO devem ser interceptadas aqui; caso contrário, o middleware criaria um
 * loop de redirecionamento (ERR_TOO_MANY_REDIRECTS) porque o frontend tenta
 * chamar /api/v1/auth/users/me/ para verificar autenticação antes de saber
 * se está autenticado.
 *
 * O matcher abaixo exclui explicitamente /api/, _next/static, _next/image e
 * favicon.ico de qualquer processamento de middleware.
 */
export function middleware(request: NextRequest) {
  // Passar adiante sem modificar — toda lógica de auth é client-side (use-auth.ts)
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
