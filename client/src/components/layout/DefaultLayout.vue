<script setup>
import HeaderLayout from './HeaderLayout.vue'
import FooterLayout from './FooterLayout.vue'
import DialogLayout from './DialogLayout.vue'
defineProps({
  footer: {
    type: Boolean,
    default: true
  }
})
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <HeaderLayout />
    <DialogLayout />
    <slot></slot>
    <FooterLayout v-show="footer" />
  </div>
</template>
