<script setup>
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import LoginForm from '@/components/user/LoginForm.vue'
import RegistrationForm from '@/components/user/RegistrationFrom.vue'
import AlertBox from '@/components/user/AlertBox.vue'
import RequestPasswordResetForm from '@/components/user/RequestPasswordResetForm.vue'
import DoPasswordResetForm from '@/components/user/DoPasswordResetForm.vue'

const DIALOGS_BY_STATE = Object.freeze(
  new Map([
    [DIALOG.LOGIN, LoginForm],
    [DIALOG.REGISTER_ENTER_DATA, RegistrationForm],
    [DIALOG.ALERT, AlertBox],
    [DIALOG.RESET_PASSWORD_REQUEST, RequestPasswordResetForm],
    [DIALOG.RESET_PASSWORD_NEW_PASSWORD, DoPasswordResetForm]
  ])
)

const dialogState = useDialogState()
dialogState.load_cookie_if_needed()
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
