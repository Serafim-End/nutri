# Admin Panel Dockerfile
# Multi-stage build: Node build + nginx serve
# Exposes HTTP on port 3001 (Cloudflare provides HTTPS externally)

# ===========================================
# Stage 1: Build
# ===========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Build args for environment variables at build time
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ===========================================
# Stage 2: Production (nginx)
# ===========================================
FROM nginx:alpine

# Install wget for healthcheck
RUN apk add --no-cache wget

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 3001
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:3001/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
