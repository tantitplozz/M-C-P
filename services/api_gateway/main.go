package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// Secret Technique: Correlation ID Middleware.
// This injects a unique ID into every request, which is then passed to downstream services and logs.
// This allows for distributed tracing across the entire stack.
func CorrelationIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		correlationID := c.GetHeader("X-Correlation-ID")
		if correlationID == "" {
			correlationID = uuid.New().String()
		}
		c.Set("correlationID", correlationID)
		c.Header("X-Correlation-ID", correlationID)
		c.Next()
	}
}

// Secret Technique: Structured Logging Middleware.
// Logs are written in JSON format with consistent fields (e.g., correlationID, serviceName).
// This makes them machine-readable and easily searchable in Loki/Grafana.
func StructuredLoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()
		latency := time.Since(start)

		log.Printf(
			`{"service": "api_gateway", "correlation_id": "%s", "status": %d, "method": "%s", "path": "%s", "latency": "%s", "ip": "%s", "user_agent": "%s"}`,
			c.GetString("correlationID"),
			c.Writer.Status(),
			c.Request.Method,
			c.Request.URL.Path,
			latency,
			c.ClientIP(),
			c.Request.UserAgent(),
		)
	}
}

func main() {
	// Set Gin mode from environment variable
	gin.SetMode(os.Getenv("GIN_MODE"))

	router := gin.New()

	// --- Middleware ---
	// Secret Technique: Use a robust, production-ready logger and recovery middleware.
	// gin.Recovery() recovers from any panics and writes a 500 if there was one.
	router.Use(gin.Recovery())
	router.Use(CorrelationIDMiddleware())
	router.Use(StructuredLoggerMiddleware())

	// Secret Technique: Configure CORS properly. Don't use wildcard '*' in production.
	// Allow only the WebUI origin.
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"http://localhost", "https://localhost"} // Replace with WebUI's actual origin in production
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Authorization", "X-Correlation-ID"}
	router.Use(cors.New(config))

	// --- Routes ---
	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "UP"})
	})

	// Placeholder for API v1 routes
	v1 := router.Group("/api/v1")
	{
		// This is where you would add handlers that proxy requests to the orchestrator
		// and other backend services.
		v1.GET("/agents", func(c *gin.Context) {
			// Example of proxying to orchestrator would go here
			c.JSON(http.StatusOK, gin.H{"message": "List of agents from orchestrator (placeholder)"})
		})
	}

	// --- Server Startup and Graceful Shutdown ---
	// Secret Technique: Implement graceful shutdown to allow in-flight requests to finish.
	srv := &http.Server{
		Addr:    ":8080",
		Handler: router,
	}

	go func() {
		// service connections
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %s\n", err)
		}
	}()

	// Wait for interrupt signal to gracefully shut down the server with a timeout.
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	log.Println("Server exiting")
}
