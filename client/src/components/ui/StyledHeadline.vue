<script setup lang="ts">
const props = defineProps<{
  text: string
}>()
const words = props.text.split(' ')
const firstWord = words[0]
const remainingWords = words.slice(1).join(' ')
</script>
<template>
  <h1
    class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
  >
    <span
      class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
      >{{ firstWord }}&nbsp;</span
    >{{ remainingWords }}
  </h1>
</template>
