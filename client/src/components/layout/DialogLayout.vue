<script setup>
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import AlertBox from '@/components/ui/AlertBox.vue'
import ConfirmBox from '@/components/ui/ConfirmBox.vue'
import LoginForm from '@/components/user/LoginForm.vue'
import RegistrationForm from '@/components/user/RegistrationFrom.vue'
import RequestPasswordResetForm from '@/components/user/RequestPasswordResetForm.vue'
import ChangePasswordForm from '@/components/user/ChangePasswordForm.vue'

const DIALOGS_BY_STATE = Object.freeze(
  new Map([
    [DIALOG.ALERT, AlertBox],
    [DIALOG.CONFIRM, ConfirmBox],
    [DIALOG.LOGIN, LoginForm],
    [DIALOG.REGISTER_ENTER_DATA, RegistrationForm],
    [DIALOG.RESET_PASSWORD_REQUEST, RequestPasswordResetForm],
    [DIALOG.CHANGE_PASSWORD, ChangePasswordForm]
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
