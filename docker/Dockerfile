FROM node:18-alpine AS base

# Install dependencies for all workspaces
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/
COPY backend/package.json backend/
RUN npm ci

# Build frontend and backend
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build --workspaces

# Production image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy backend dist
COPY --from=builder /app/backend/dist ./backend/dist
COPY --from=builder /app/backend/package.json ./backend/
COPY --from=builder /app/node_modules ./node_modules
COPY package.json ./

EXPOSE 3001
CMD ["node", "backend/dist/index.js"]
