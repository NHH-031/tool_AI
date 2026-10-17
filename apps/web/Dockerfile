# ==============================================================================
# Dockerfile for AI Whiteboard Video Studio Web Frontend (Next.js)
# ==============================================================================
FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies based on package.json
COPY package.json package-lock.json* ./
RUN npm install

# Copy application source
COPY . .

# Build Next.js web application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

EXPOSE 3000

ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

CMD ["npm", "run", "start"]
