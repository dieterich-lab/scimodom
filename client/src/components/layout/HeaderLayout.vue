<script setup>
import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'

import { DIALOG, useDialogState } from '@/utils/DialogState.js'
const dialogState = useDialogState()

function login() {
  dialogState.$patch({
    state: DIALOG.LOGIN,
    email: null,
    message: null
  })
}

function signUp() {
  dialogState.$patch({
    state: DIALOG.REGISTER_ENTER_DATA,
    email: null,
    message: null
  })
}
</script>

<template>
  <header
    class="top-0 z-20 sticky bg-white opacity-90 border-b border-surface-200 dark:bg-surface-900 dark:opacity-100 dark:border-surface-800"
  >
    <div
      class="p-1 bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100%"
    />
    <div class="mx-auto w-full max-w-screen-2xl p-2 py-6 lg:py-8 flex flex-wrap items-center">
      <div class="flex flex-wrap 2xl:w-4/5 xl:w-auto">
        <ScimodomLogo />
        <NavigationBar />
      </div>
      <div class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0 gap-4">
        <Button
          :disabled="true"
          label="Login"
          @click="login()"
          icon="pi pi-user"
          size="small"
          raised
        />
        <Button
          :disabled="true"
          label="Sign Up"
          @click="signUp()"
          icon="pi pi-user-plus"
          size="small"
          severity="secondary"
          raised
        />
      </div>
    </div>
  </header>
</template>
