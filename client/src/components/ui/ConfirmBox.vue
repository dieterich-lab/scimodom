<script setup>
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import FromBox from '@/components/ui/FormBox.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'
import PrimaryDialogStyle from '@/ui_styles/PrimaryDialogStyle.js'

const dialogState = useDialogState()

function ok() {
  dialogState.confirm()
}

function cancel() {
  dialogState.state = DIALOG.NONE
}
</script>

<template>
  <form @submit="ok">
    <FromBox :ui-style="PrimaryDialogStyle">
      <FormButtonGroup>
        <FormButton type="submit" :ui-style="PrimaryDialogStyle">Confirm</FormButton>
        <FormButton @on-click="cancel()" :ui-style="PrimaryDialogStyle">Cancel</FormButton>
      </FormButtonGroup>
    </FromBox>
  </form>
</template>
