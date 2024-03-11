<template>
  <nav class="flex flex-wrap font-ham text-4xl [&>*]:mr-6 dark:text-white/80">
    <RouterLink :to="{ name: 'search' }">
      <span>Search</span>
    </RouterLink>

    <RouterLink :to="{ name: 'browse' }">
      <span>Browse</span>
    </RouterLink>

    <RouterLink :to="{ name: 'compare' }">
      <span>Compare</span>
    </RouterLink>

    <RouterLink :to="{ name: 'download' }">
      <span>Download</span>
    </RouterLink>

    <RouterLink :to="{ name: 'documentation' }">
      <span>Documentation</span>
    </RouterLink>
  </nav>
</template>
