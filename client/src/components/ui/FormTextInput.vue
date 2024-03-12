<script setup>
const model = defineModel()
const props = defineProps(['error', 'type'])
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" class="text-primary-50 font-semibold">
      <slot></slot>
    </label>
    <InputText
      id="field"
      v-model="model"
      :class="{ 'p-invalid': error }"
      class="bg-white/20 border-0 p-4 text-primary-50"
      :type="type || 'text'"
    />
    <p class="text-primary-900 p-error">{{ error }}&nbsp;</p>
  </div>
</template>
