<script setup lang="ts">
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import DialogBox from '@/components/ui/DialogBox.vue'
import DialogButtonGroup from '@/components/ui/DialogButtonGroup.vue'
import DialogButton from '@/components/ui/DialogButton.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/ui_style'

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
    <DialogBox :ui-style="PRIMARY_DIALOG_STYLE">
      <DialogButtonGroup>
        <DialogButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">Confirm</DialogButton>
        <DialogButton @on-click="cancel()" :ui-style="PRIMARY_DIALOG_STYLE">Cancel</DialogButton>
      </DialogButtonGroup>
    </DialogBox>
  </form>
</template>
