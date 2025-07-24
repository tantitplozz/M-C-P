package main

import (
	"log"
	"time"
)

// Agent represents a generic worker in the OMNI AGENT STACK.
type Agent struct {
	ID   string
	Task string
}

// NewAgent creates a new agent instance.
func NewAgent(id, task string) *Agent {
	return &Agent{
		ID:   id,
		Task: task,
	}
}

// Run starts the agent's main processing loop.
// Secret Technique: This loop should connect to the Orchestrator via gRPC or a message queue (e.g., Redis Pub/Sub)
// to receive tasks. This decouples the agent from the Orchestrator, allowing for independent scaling and updates.
func (a *Agent) Run() {
	log.Printf("Agent %s starting with task: %s\n", a.ID, a.Task)

	// Main loop
	for {
		log.Printf("Agent %s is working...", a.ID)
		// 1. Dequeue task from Redis/NATS or receive from Orchestrator gRPC stream.
		// 2. Execute the task logic.
		// 3. Report status/results back to the Orchestrator.
		// 4. Sleep or wait for the next task.
		time.Sleep(15 * time.Second)
	}
}

func main() {
	// In a real scenario, the agent would be initialized with a unique ID
	// and would register itself with the Orchestrator.
	agent := NewAgent("template-001", "generic_processing")

	// The agent's run loop is blocking.
	agent.Run()
}
