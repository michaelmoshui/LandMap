# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/playwright:v1.49.1-jammy
WORKDIR /e2e
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

# Wait for the proxy to be reachable, then run the suite. The app URL is
# provided via E2E_BASE_URL (see docker-compose.e2e.yml). Use the http-get://
# scheme so wait-on issues a GET (the health route does not allow HEAD).
CMD ["sh", "-c", "npx wait-on -t 60000 $(echo ${E2E_BASE_URL}/api/health | sed 's|^http://|http-get://|') && npx playwright test"]
