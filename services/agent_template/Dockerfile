# OMNI AGENT STACK - Agent Template Dockerfile
# This Dockerfile is a template for creating new, specialized agents.
# It follows the same secure and efficient multi-stage build pattern.

# --- Build Stage ---
FROM golang:1.22-alpine AS builder

ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -ldflags="-w -s" -o /bin/agent .

# --- Production Stage ---
FROM gcr.io/distroless/static-debian11

COPY --from=builder /bin/agent /

USER nonroot:nonroot

# This agent doesn't expose a port as it communicates with the orchestrator
# via message queues or gRPC, not direct HTTP requests.

ENTRYPOINT ["/agent"]
