# CredFlow Frontend - Next.js
# Node.js 20+

FROM node:20-alpine as base

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Install dependencies
    COPY package.json ./
    RUN npm install

# Copy source code
COPY . .

# Development stage
FROM base as development

EXPOSE 3000

CMD ["npm", "run", "dev"]

# Production stage
FROM base as builder

RUN npm run build

FROM node:20-alpine as production

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]