<script setup>
const props = defineProps(['type', 'onClick'])
</script>
<template>
  <Button
    @click="$emit('onClick')"
    :type="type || 'button'"
    class="p-4 w-full text-primary-50 border border-white-alpha-30"
  >
    <slot></slot>
  </Button>
</template>
