FROM node:20-alpine

WORKDIR /app

# Install deps
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY tsconfig.json ./
COPY src ./src

# Build
RUN npm run build

# Cloud Run listens on PORT env var
ENV PORT=8080

CMD ["npm", "start"]
