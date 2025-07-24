# OMNI AGENT STACK - API Gateway Dockerfile
# Secret Technique: Multi-stage builds.
# Stage 1: Build the Go binary in a dedicated build environment.
# Stage 2: Copy ONLY the compiled binary into a minimal, hardened production image.
# This results in a tiny, secure final image with no source code or build tools.

# --- Build Stage ---
FROM golang:1.22-alpine AS builder

# Set necessary environment variables
ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64

# Set the working directory
WORKDIR /app

# Copy go.mod and go.sum to download dependencies first
# This leverages Docker's layer caching. Dependencies are only re-downloaded if go.mod/go.sum changes.
COPY go.mod go.sum ./
RUN go mod download

# Copy the source code
COPY . .

# Build the Go application
# -ldflags="-w -s" strips debug information, reducing the binary size.
# -o /bin/api_gateway outputs the compiled binary to a specific location.
RUN go build -ldflags="-w -s" -o /bin/api_gateway .

# --- Production Stage ---
# Use a minimal, non-root base image for the final stage.
# "scratch" is the smallest possible image, but "gcr.io/distroless/static-debian11"
# provides some basic necessities like CA certificates without a shell or package manager.
FROM gcr.io/distroless/static-debian11

# Copy the compiled binary from the builder stage
COPY --from=builder /bin/api_gateway /

# Copy any other necessary assets (e.g., templates, configs) if they exist
# COPY --from=builder /app/templates/ /templates/

# Set the user to non-root for security
USER nonroot:nonroot

# Expose the port the application runs on
EXPOSE 8080

# Set the entrypoint for the container
ENTRYPOINT ["/api_gateway"]