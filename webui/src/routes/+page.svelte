<svelte:head>
  <title>Dashboard - OMNI AGENT STACK</title>
</svelte:head>

<div class="container mx-auto p-6">
  <h1 class="text-3xl font-bold mb-6">System Dashboard</h1>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <!-- Stat Card 1 -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 class="text-xl font-semibold text-gray-400">Active Agents</h2>
      <p class="text-4xl font-bold text-green-400">12</p>
    </div>

    <!-- Stat Card 2 -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 class="text-xl font-semibold text-gray-400">Tasks Completed (24h)</h2>
      <p class="text-4xl font-bold text-blue-400">1,284</p>
    </div>

    <!-- Stat Card 3 -->
    <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 class="text-xl font-semibold text-gray-400">System Health</h2>
      <p class="text-4xl font-bold text-green-400">99.9%</p>
    </div>
  </div>

  <div class="mt-8 bg-gray-800 p-6 rounded-lg shadow-lg">
    <h2 class="text-2xl font-bold mb-4">Recent Activity</h2>
    <ul>
      <li class="border-b border-gray-700 py-2">Agent 'vision-alpha-01' completed task 'image_analysis_4a2v'.</li>
      <li class="border-b border-gray-700 py-2">Agent 'data-miner-03' started task 'fetch_market_data_q3'.</li>
      <li class="border-b border-gray-700 py-2">System scaled up to 15 active agents due to increased load.</li>
    </ul>
  </div>
</div>
