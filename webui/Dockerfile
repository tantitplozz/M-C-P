# OMNI AGENT STACK - WebUI (SvelteKit) Dockerfile
# Secret Technique: Multi-stage build for Node.js applications.
# Stage 1: Install dependencies and build the static assets.
# Stage 2: Use a lightweight web server (Caddy) to serve the built assets.
# This avoids shipping the entire Node.js runtime and dependencies in the final image.

# --- Build Stage ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package.json and lock file
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the SvelteKit application
# The adapter-node will create a standalone Node.js server in the build directory.
RUN npm run build

# --- Production Stage ---
# We are using a custom Node server output from SvelteKit adapter-node.
# A minimal Node.js image is used for the production stage.
FROM node:20-alpine

WORKDIR /app

# Set NODE_ENV to production
ENV NODE_ENV=production

# Copy the built output from the builder stage
COPY --from=builder /app/build ./
COPY --from=builder /app/node_modules ./node_modules

# Expose the port the app will run on
EXPOSE 3000

# The command to run the SvelteKit node server
CMD ["node", "index.js"]