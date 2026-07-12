# =============================================================================
# Stage 1: Build — install dependencies and compile production bundle
# =============================================================================
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}

COPY . .
RUN npm run build


# =============================================================================
# Stage 2: Serve — production nginx image, no Node.js
# =============================================================================
FROM nginx:stable-alpine AS runtime

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
