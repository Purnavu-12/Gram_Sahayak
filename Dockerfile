# ── Stage 1: Build the React frontend ──────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# ── Stage 2: Python runtime ───────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Python deps
COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application code
COPY token_server.py scheme_lookup.py schemes.db ./

# Copy built frontend from stage 1
COPY --from=frontend-build /app/dist ./dist

EXPOSE 8081
CMD ["python", "token_server.py"]
