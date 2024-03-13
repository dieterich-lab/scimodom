<script setup>
const model = defineModel()
const props = defineProps({
  error: {
    required: true
  },
  rows: {
    type: Number,
    required: false,
    default: 5
  },
  cols: {
    type: Number,
    required: false,
    default: 50
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
    default: 'ring-red-700'
  }
})
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.labelCls">
      <slot></slot>
    </label>
    <Textarea
      id="field"
      v-model="model"
      autoResize
      rows="props.rows"
      cols="props.cols"
      :placeholder="props.placeholder"
      :class="error ? props.errCls : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.errIconCls : ''" />
      <span :class="['pl-1 place-self-center', props.errMsgCls]">{{ error }}&nbsp;</span>
    </span>
  </div>
</template>
