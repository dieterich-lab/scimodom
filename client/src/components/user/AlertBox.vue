<script setup>
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import FromBox from '@/components/ui/FormBox.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'
import PrimaryDialogStyle from '@/ui_styles/PrimaryDialogStyle.js'

const dialogState = useDialogState()

function ok() {
  dialogState.state = DIALOG.NONE
}
</script>

<template>
  <form @submit="ok">
    <FromBox :ui-style="PrimaryDialogStyle">
      <FormButtonGroup>
        <FormButton type="submit" :ui-style="PrimaryDialogStyle">OK</FormButton>
      </FormButtonGroup>
    </FromBox>
  </form>
</template>
