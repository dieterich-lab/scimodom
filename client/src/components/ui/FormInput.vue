<script setup>
import { useField } from 'vee-validate'

const props = defineProps({
  input: String,
  type: String
})

// input must be reactive
const { value, errorMessage } = useField(() => props.input)
</script>

<template>
  <InputText
    id="value"
    v-model="value"
    class="bg-white/20 border-0 p-4 text-primary-50"
    :type="type || 'text'"
  ></InputText>
  <p class="text-primary-900">{{ errorMessage }}</p>
</template>
