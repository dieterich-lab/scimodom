<script setup lang="ts">
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import FromBox from '@/components/ui/FormBox.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/UiStyle'

const dialogState = useDialogState()

function ok() {
  dialogState.state = DIALOG.NONE
}
</script>

<template>
  <form @submit="ok">
    <FromBox :ui-style="PRIMARY_DIALOG_STYLE">
      <FormButtonGroup>
        <FormButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">OK</FormButton>
      </FormButtonGroup>
    </FromBox>
  </form>
</template>
