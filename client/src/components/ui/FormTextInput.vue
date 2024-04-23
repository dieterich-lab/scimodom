<script setup>
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
  isLogin: {
    type: Boolean,
    required: false,
    default: false
  },
  isSignIn: {
    type: Boolean,
    required: false,
    default: false
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

// pt style for login and sign in
const loginStyle = {
  root: ({ props, context, parent }) => ({
    class: [
      'bg-primary-50/25 dark:bg-surface-900/20',
      {
        'ring-primary-500/20 dark:ring-primary-500/20': parent.instance.$name != 'InputGroup'
      }
    ]
  })
}
// TODO: change with FormBox color
const signInStyle = {
  root: ({ props, context, parent }) => ({
    class: [
      'bg-primary-50/25 dark:bg-surface-900/20',
      {
        'ring-primary-500/20 dark:ring-primary-500/20': parent.instance.$name != 'InputGroup'
      }
    ]
  })
}
const pt = props.isLogin ? loginStyle : props.isSignIn ? signInStyle : {}
const ptOptions = props.isLogin || props.isSignIn ? { mergeProps: true } : {}
</script>

<template>
  <div class="inline-flex flex-col gap-2">
    <label for="field" :class="props.labelCls">
      <slot></slot>
    </label>
    <InputText
      id="field"
      v-model="model"
      :type="type"
      :placeholder="props.placeholder"
      :disabled="props.disabled"
      :pt="pt"
      :ptOptions="ptOptions"
      :class="error ? props.errCls : ''"
    />
    <span class="inline-flex items-baseline">
      <i :class="error ? props.errIconCls : ''" />
      <span :class="['pl-1 place-self-center', props.errMsgCls]">{{ error }}&nbsp;</span>
    </span>
  </div>
</template>
