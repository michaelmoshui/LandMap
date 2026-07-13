# syntax=docker/dockerfile:1

# ---- deps: install node modules (cached across builds) -----------------
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- test: run Vitest unit tests ---------------------------------------
FROM deps AS test
COPY . .
CMD ["npm", "run", "test"]

# ---- build: produce static assets --------------------------------------
FROM deps AS build
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
COPY . .
RUN npm run build

# ---- prod: serve static assets with nginx ------------------------------
FROM nginx:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
