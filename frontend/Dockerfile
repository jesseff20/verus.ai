# syntax=docker/dockerfile:1
# Frontend Next.js (output: 'standalone') para deploy no Dokploy.

# Stage 1 — dependências
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

# Stage 2 — build
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Variáveis NEXT_PUBLIC_* são inlinadas no bundle do cliente em build time.
# NEXT_PUBLIC_API_URL vazio = URLs relativas no cliente; Traefik roteia /api/* para o backend.
# BACKEND_URL é runtime-only (não precisa de ARG) — injetado pelo docker-compose no contêiner.
ARG NEXT_PUBLIC_API_URL=""
ARG NEXT_PUBLIC_APP_NAME="Verus.AI"
ARG NEXT_PUBLIC_APP_VERSION="1.0.0"
ARG NEXT_PUBLIC_API_BASE_PATH="/api/v1"
ARG NEXT_PUBLIC_TINYMCE_API_KEY=""
# BACKEND_URL é necessário em build time para que os rewrites em next.config.js
# sejam gerados com o hostname correto (verus-backend:8000 na rede Docker).
# O valor padrão corresponde ao nome do serviço no docker-compose.dokploy.yml.
ARG BACKEND_URL="http://verus-backend:8000"
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME \
    NEXT_PUBLIC_APP_VERSION=$NEXT_PUBLIC_APP_VERSION \
    NEXT_PUBLIC_API_BASE_PATH=$NEXT_PUBLIC_API_BASE_PATH \
    NEXT_PUBLIC_TINYMCE_API_KEY=$NEXT_PUBLIC_TINYMCE_API_KEY \
    BACKEND_URL=$BACKEND_URL \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production
RUN npm run build

# Stage 3 — runtime (standalone)
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
