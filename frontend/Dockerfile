# Frontend Dockerfile - Multi-stage build for HSA Manager React app
# Build stage: Install dependencies and build the React application
FROM node:18-alpine as builder

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with clean installation (including dev dependencies for build)
RUN npm ci --silent

# Copy all source code
COPY . .

# Build the application for production (skip TypeScript checking for Docker build)
RUN ./node_modules/.bin/vite build

# Production stage: Serve with nginx
FROM nginx:1.25-alpine

# Install dumb-init for proper signal handling and curl for health checks
RUN apk add --no-cache dumb-init curl

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create nginx runtime directories and set ownership
RUN mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp \
    && chown -R appuser:appuser /var/cache/nginx \
    && chown -R appuser:appuser /usr/share/nginx/html \
    && chown -R appuser:appuser /var/log/nginx \
    && chown appuser:appuser /etc/nginx/nginx.conf

# Create nginx pid file and set ownership
RUN touch /var/run/nginx.pid \
    && chown appuser:appuser /var/run/nginx.pid

# Switch to non-root user
USER appuser

# Health check using curl to test nginx response
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Start command using dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]