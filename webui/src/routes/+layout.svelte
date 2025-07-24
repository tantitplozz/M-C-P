<script>
  import "../app.css";
</script>

<div class="min-h-screen bg-gray-900 text-gray-100">
  <header class="bg-gray-800 shadow">
    <nav class="container mx-auto px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="text-xl font-semibold text-white">
          OMNI AGENT STACK
        </div>
        <div>
          <a href="/" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
          <a href="/agents" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Agents</a>
          <a href="/monitoring" class="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Monitoring</a>
        </div>
      </div>
    </nav>
  </header>
  <main>
    <slot />
  </main>
</div>