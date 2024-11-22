<script setup lang="ts">
import { type Component, computed, ref } from 'vue'
import Dialog from 'primevue/dialog'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import AlertBox from '@/components/ui/AlertBox.vue'
import ConfirmBox from '@/components/ui/ConfirmBox.vue'
import LoginForm from '@/components/user/LoginForm.vue'
import RegistrationForm from '@/components/user/RegistrationFrom.vue'
import RequestPasswordResetForm from '@/components/user/RequestPasswordResetForm.vue'
import ChangePasswordForm from '@/components/user/ChangePasswordForm.vue'
import ErrorAlertBox from '@/components/ui/ErrorAlertBox.vue'

const DIALOGS_BY_STATE: Readonly<Map<DIALOG, Component>> = new Map([
  [DIALOG.ALERT, AlertBox],
  [DIALOG.ERROR_ALERT, ErrorAlertBox],
  [DIALOG.CONFIRM, ConfirmBox],
  [DIALOG.LOGIN, LoginForm],
  [DIALOG.REGISTER_ENTER_DATA, RegistrationForm],
  [DIALOG.RESET_PASSWORD_REQUEST, RequestPasswordResetForm],
  [DIALOG.CHANGE_PASSWORD, ChangePasswordForm]
])

const dialogState = useDialogState()
const showDialog = computed(() => dialogState.state !== DIALOG.NONE)
const component = computed(() => DIALOGS_BY_STATE.get(dialogState.state))
dialogState.load_cookie_if_needed()
const show = ref<boolean>(true)
</script>

<template>
  <Dialog
    v-if="showDialog"
    v-model:visible="show"
    modal
    :pt="{
      root: 'border-none',
      mask: {
        style: 'backdrop-filter: blur(2px)'
      }
    }"
    :close-on-escape="false"
  >
    <template #container>
      <component :is="component"></component>
    </template>
  </Dialog>
</template>
