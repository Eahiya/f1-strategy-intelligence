# F1 Strategy Platform v4.0 - Production Infrastructure Edition
# Frontend Dockerfile - React SPA

# Build stage
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# Production stage - NGINX
FROM nginx:alpine

# Install security updates
RUN apk --no-cache add curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/

# Copy built React app
COPY --from=builder /app/build /usr/share/nginx/html

# Create nginx user
RUN adduser -D -H -u 1000 -s /sbin/nologin nginx-user

# Set permissions
RUN chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

# Expose port
EXPOSE 80

# Run nginx as non-root
USER nginx-user

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
