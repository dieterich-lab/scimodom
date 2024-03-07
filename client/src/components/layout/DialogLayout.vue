<script setup>
import { DIALOG, useDialogState } from '@/utils/dialogState.js'
import LoginForm from '@/components/user/LoginForm.vue'

const DIALOGS_BY_STATE = Object.freeze(new Map([[DIALOG.LOGIN, LoginForm]]))

const dialogState = useDialogState()
dialogState.load_cookie_if_needed()
let current_component = null
switch (dialogState.state) {
  case DIALOG.LOGIN:
    current_component = LoginForm
    break
}
const show = true
</script>

<template>
  <Dialog
    v-if="dialogState.state !== DIALOG.NONE"
    v-model:visible="show"
    modal
    :pt="{
      root: 'border-none',
      mask: {
        style: 'backdrop-filter: blur(2px)'
      }
    }"
  >
    <template #container="{ closeCallback }">
      <component :is="DIALOGS_BY_STATE.get(dialogState.state)"></component>
    </template>
  </Dialog>
</template>
