<script setup>
import AbstractStyle from '@/ui_styles/AbstractStyle'
import DefaultStyle from '@/ui_styles/DefaultStyle'

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
  uiStyle: {
    type: AbstractStyle,
    required: false,
    default: DefaultStyle
  }
})
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.uiStyle.labelClasses()">
      <slot></slot>
    </label>
    <Textarea
      id="field"
      v-model="model"
      autoResize
      rows="props.rows"
      cols="props.cols"
      :placeholder="props.placeholder"
      :class="error ? props.uiStyle.errorClasses() : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.uiStyle.errorIconClasses() : ''" />
      <span :class="['pl-1 place-self-center', props.uiStyle.errorTextClasses()]"
        >{{ error }}&nbsp;</span
      >
    </span>
  </div>
</template>
