package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
)

// Secret Technique: This service will eventually contain the core logic for
// agent lifecycle management, task scheduling, and self-healing.
// For now, it's a simple service with a health check.

func main() {
	gin.SetMode(os.Getenv("GIN_MODE"))

	router := gin.New()
	router.Use(gin.Recovery())
	// In a real scenario, we'd add Correlation ID and Structured Logging middleware here too.

	// --- Routes ---
	router.GET("/health", func(c *gin.Context) {
		// A real health check would also verify connections to Postgres and Redis.
		c.JSON(http.StatusOK, gin.H{"status": "UP", "service": "orchestrator"})
	})

	// Placeholder for orchestrator-specific logic
	// e.g., router.POST("/api/v1/tasks", taskHandler.Create)

	// --- Server Startup and Graceful Shutdown ---
	srv := &http.Server{
		Addr:    ":8081", // Orchestrator runs on a different port
		Handler: router,
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %s\n", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down orchestrator server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("Orchestrator server forced to shutdown:", err)
	}

	log.Println("Orchestrator server exiting")
}