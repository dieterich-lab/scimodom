<script setup>
defineProps({
  icon: {
    type: String,
    required: true
  },
  route: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="max-w-sm p-6 bg-ctransparent border border-cborder rounded-lg shadow">
    <h5 class="mb-2 text-2xl font-semibold tracking-tight text-gray-900">
      <i :class="icon" class="p-0 px-1" />
      <slot name="title"></slot>
    </h5>
    <p class="mb-3 font-normal text-gray-500">
      <slot name="content"></slot>
    </p>
    <a :href="route" class="inline-flex items-center text-crmapblue0 hover:underline">
      <slot name="link"></slot>
      <i class="pi pi-arrow-up-right ml-2" />
    </a>
  </div>
</template>
