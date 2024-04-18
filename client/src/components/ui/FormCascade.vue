<script setup>
// provides a custom wrapper for the PrimeVue Cascade component
// to be used in a form, with default grouping - hard coded "key"
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
  optionGroupLabel: {
    type: String,
    required: false,
    default: 'label'
  },
  optionGroupChildren: {
    type: Array,
    required: false,
    default: ['child1']
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
    if (!(props.modelValue == '' || props.modelValue == undefined)) {
      return props.options
        .filter((a) => a[props.optionGroupChildren].some((b) => b.key == props.modelValue))
        .map((c) => c[props.optionGroupChildren])[0]
        .filter((d) => d.key == props.modelValue)[0]
    }
  },
  set(value) {
    emit('update:modelValue', value.key)
  }
})
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.labelCls">
      <slot></slot>
    </label>
    <CascadeSelect
      id="field"
      v-model="computedModel"
      :options="props.options"
      :optionLabel="props.optionsLabel"
      :optionGroupLabel="props.optionGroupLabel"
      :optionGroupChildren="props.optionGroupChildren"
      :placeholder="props.placeholder"
      :class="error ? props.errCls : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.errIconCls : ''" />
      <span :class="['pl-1 place-self-center', props.errMsgCls]">{{ error }}&nbsp;</span>
    </span>
  </div>
</template>
