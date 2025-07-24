# OMNI AGENT STACK - Orchestrator Dockerfile
# Following the same multi-stage build pattern for a minimal and secure final image.

# --- Build Stage ---
FROM golang:1.22-alpine AS builder

ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -ldflags="-w -s" -o /bin/orchestrator .

# --- Production Stage ---
FROM gcr.io/distroless/static-debian11

COPY --from=builder /bin/orchestrator /

USER nonroot:nonroot

# Expose the port the application runs on
EXPOSE 8081

ENTRYPOINT ["/orchestrator"]
