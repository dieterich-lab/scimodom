<script setup>
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import FromBox from '@/components/ui/FormBox.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'

const dialogState = useDialogState()

function ok() {
  dialogState.state = DIALOG.NONE
}
</script>

<template>
  <form @submit="ok">
    <FromBox>
      {{ dialogState.message }}
      <FormButtonGroup>
        <FormButton type="submit">OK</FormButton>
      </FormButtonGroup>
    </FromBox>
  </form>
</template>
