<script setup>
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import LoginForm from '@/components/user/LoginForm.vue'
import RegistrationForm from '@/components/user/RegistrationFrom.vue'
import RegistrationCheckEmail from '@/components/user/AlertBox.vue'

const DIALOGS_BY_STATE = Object.freeze(
  new Map([
    [DIALOG.LOGIN, LoginForm],
    [DIALOG.REGISTER_ENTER_DATA, RegistrationForm],
    [DIALOG.REGISTER_CHECK_EMAIL, RegistrationCheckEmail]
  ])
)

const dialogState = useDialogState()
dialogState.load_cookie_if_needed()
const show = true
console.log(`dialogState: ${dialogState.state.description}`)
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
