<template>
  <div class="min-h-screen bg-gray-100 text-gray-900 font-sans">
    <!-- Top Navbar -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <h1 class="text-2xl font-semibold text-gray-800 flex items-center gap-2">
          <i class="ri-bar-chart-line text-indigo-500 text-3xl"></i>
          MSS – Monthly.............
        </h1>

        <!-- Right Actions (optional) -->
        <div class="flex items-center gap-3">
          <button class="btn btn-primary">
            Refresh
          </button>
        </div>
      </div>
    </header>

    <!-- Main Page Container -->
    <main class="max-w-7xl mx-auto px-6 py-6">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: "App"
};
</script>

<style scoped>
/* Optional: Slightly improve scroll behavior */
html {
  scroll-behavior: smooth;
}
</style>
