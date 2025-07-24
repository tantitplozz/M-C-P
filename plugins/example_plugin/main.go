package main

import "fmt"

// Secret Technique: Go plugins are compiled as shared objects (.so files).
// The Orchestrator can dynamically load and unload these plugins at runtime without restarting.
// This allows for extreme modularity and on-the-fly capability extension.

// The plugin must export symbols that the Orchestrator knows how to look for.
// By convention, we can export a struct that implements a well-defined interface.

// PluginName is a unique identifier for this plugin.
var PluginName = "ExamplePlugin"

// Plugin is the struct that will be loaded by the orchestrator.
type Plugin struct{}

// Execute is the main function of the plugin.
// It receives a context and a payload and returns a result.
func (p Plugin) Execute(context map[string]interface{}, payload []byte) (string, error) {
	fmt.Printf("ExamplePlugin executed with context: %v\n", context)
	return fmt.Sprintf("Processed payload: %s", string(payload)), nil
}

// Export the plugin instance so it can be found by the orchestrator.
var ExportedPlugin = Plugin{}
