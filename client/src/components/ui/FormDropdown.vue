<script setup>
// provides a custom wrapper for the PrimeVue Dropdown component
// to be used in a form - hard coded "id"
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    required: true
  },
  error: {
    required: true
  },
  options: {
    type: Array,
    required: true
  },
  optionsLabel: {
    type: String,
    required: false,
    default: 'label'
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
const emit = defineEmits(['update:modelValue'])
// boiler plate... there is surely a nicer solution?!
const computedModel = computed({
  get() {
    return props.options.filter((item) => item.id == props.modelValue)[0]
  },
  set(value) {
    emit('update:modelValue', value.id)
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
      v-model="computedModel"
      :options="props.options"
      :optionLabel="props.optionsLabel"
      :placeholder="props.placeholder"
      :class="error ? props.errCls : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.errIconCls : ''" />
      <span :class="['pl-1 place-self-center', props.errMsgCls]">{{ error }}&nbsp;</span>
    </span>
  </div>
</template>
