<script setup>
import InputText from 'primevue/inputtext'

const model = defineModel()
const props = defineProps(['error', 'type'])
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" class="text-primary-50 font-semibold">
      <slot></slot>
    </label>
    <InputText id="field" v-model="model" :class="{ 'p-invalid': error }" :type="type || 'text'" />
    <!--            class="bg-white/20 border-0 p-4 text-primary-50"-->
    <p class="text-primary-900 p-error">{{ error }}</p>
    <!--        <label for="email">Email</label>-->
    <!--        <InputText v-model="email" :class="{ 'p-invalid': errors.email }"/>-->
  </div>
</template>
