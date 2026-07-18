# =============================================================================
# Stage 1: Build — install dependencies and compile production bundle
# =============================================================================
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Vite build-time variables are injected via vite.env, which is generated
# dynamically by CI from APP_ENV. Every key in APP_ENV that starts with
# VITE_ is written into this file and sourced into the shell environment
# before the build. This approach is future-proof: adding a new VITE_*
# variable to APP_ENV requires zero Dockerfile changes.
COPY . .
COPY vite.env /tmp/vite.env
RUN set -a && . /tmp/vite.env && set +a && npm run build


# =============================================================================
# Stage 2: Serve — production nginx image, no Node.js
# =============================================================================
FROM nginx:stable-alpine AS runtime

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
