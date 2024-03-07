<script setup>
import { ref } from 'vue'
import { Form } from 'vee-validate'

const props = defineProps(['mySubmit', 'validationSchema'])
const form = ref(null)
defineExpose({ form })
</script>

<template>
  <Form @submit="mySubmit" :validation-schema="validationSchema" ref="form">
    <div
      class="flex flex-col px-8 py-8 gap-4"
      style="
        border-radius: 12px;
        background-image: radial-gradient(
          circle at center,
          rgb(var(--primary-600)),
          rgb(var(--primary-500)),
          rgb(var(--primary-400))
        );
      "
    >
      <slot name="fields"></slot>
      <div class="flex items-center gap-4">
        <slot name="buttons"></slot>
      </div>
    </div>
  </Form>
</template>
