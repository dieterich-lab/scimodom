<script setup>
import AbstractStyle from '@/ui_styles/AbstractStyle.js'
import DefaultStyle from '@/ui_styles/DefaultStyle.js'
const model = defineModel()
const props = defineProps({
  error: {
    required: true
  },
  type: {
    type: String,
    required: false,
    default: 'text'
  },
  disabled: {
    type: Boolean,
    required: false,
    default: false
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

// pt style for login and sign in
const pt = {
  root: ({ _1, _2, parent }) => ({
    class: [
      parent.instance.$name === 'InputGroup'
        ? props.uiStyle.inputTextGroupClasses()
        : props.uiStyle.inputTextDefaultClasses()
    ]
  })
}
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.uiStyle.labelClasses()">
      <slot></slot>
    </label>
    <InputText
      id="field"
      v-model="model"
      :type="type"
      :placeholder="props.placeholder"
      :disabled="props.disabled"
      :pt="pt"
      :ptOptions="{ mergeProps: true }"
      :class="error ? props.uiStyle.errorClasses() : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.uiStyle.errorIconClasses() : ''" />
      <span :class="['pl-1 place-self-center', props.uiStyle.errorClasses]">{{ error }}&nbsp;</span>
    </span>
  </div>
</template>
