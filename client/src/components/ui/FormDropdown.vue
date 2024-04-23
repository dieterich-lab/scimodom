<script setup>
// provides a custom wrapper for the PrimeVue Dropdown component
// to be used in a form
import { ref, computed } from 'vue'

const emit = defineEmits(['change'])
const model = defineModel()
const props = defineProps({
  error: {
    required: true
  },
  options: {
    type: Array,
    required: true
  },
  optionLabel: {
    type: String,
    required: false,
    default: 'label'
  },
  optionValue: {
    type: String,
    required: false,
    default: 'value'
  },
  placeholder: {
    type: String,
    required: false,
    default: ''
  },
  labelCls: {
    type: String,
    required: false,
    default: 'text-primary-500 font-semibold'
  },
  errMsgCls: {
    type: String,
    required: false,
    default: 'text-red-700'
  },
  errIconCls: {
    type: String,
    required: false,
    default: 'pi pi-times-circle place-self-center text-red-700'
  },
  // overwrites component style in case of error
  errCls: {
    type: String,
    required: false,
    default: '!ring-red-700'
  }
})
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.labelCls">
      <slot></slot>
    </label>
    <Dropdown
      id="field"
      v-model="model"
      @change="$emit('change', $event.value)"
      :options="props.options"
      :optionLabel="props.optionLabel"
      :optionValue="props.optionValue"
      :placeholder="props.placeholder"
      :class="error ? props.errCls : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.errIconCls : ''" />
      <span :class="['pl-1 place-self-center', props.errMsgCls]">{{ error }}&nbsp;</span>
    </span>
  </div>
</template>
