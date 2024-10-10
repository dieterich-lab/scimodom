<script setup lang="ts">
defineProps<{
  icon: string
  route: string
}>()
</script>

<template>
  <div class="max-w-sm p-4 bg-transparent rounded-lg shadow-xl dark:shadow-surface-800/50">
    <h5 class="mb-2 text-2xl font-semibold tracking-tight text-gray-900 dark:text-white/80">
      <i :class="icon" class="p-0 px-1 dark:text-white/80" />
      <slot name="title"></slot>
    </h5>
    <p class="mb-3 font-normal text-gray-600 dark:text-surface-400">
      <slot name="content"></slot>
    </p>
    <RouterLink
      :to="{ name: route }"
      class="inline-flex items-center font-semibold text-primary-500 hover:text-secondary-500"
    >
      <slot name="link"></slot>
      <i class="pi pi-arrow-up-right ml-2" />
    </RouterLink>
  </div>
</template>
