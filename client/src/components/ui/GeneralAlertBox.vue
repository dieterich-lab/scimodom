<script setup lang="ts">
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import DialogBox from '@/components/ui/DialogBox.vue'
import FormButtonGroup from '@/components/ui/DialogButtonGroup.vue'
import DialogButton from '@/components/ui/DialogButton.vue'
import { PRIMARY_DIALOG_STYLE, type UiStyle } from '@/utils/ui_style'

withDefaults(
  defineProps<{
    uiStyle?: UiStyle
  }>(),
  {
    uiStyle: () => PRIMARY_DIALOG_STYLE
  }
)

const dialogState = useDialogState()

function ok() {
  dialogState.state = DIALOG.NONE
}
</script>

<template>
  <form @submit="ok">
    <DialogBox :ui-style="uiStyle">
      <FormButtonGroup>
        <DialogButton type="submit" :ui-style="uiStyle">OK</DialogButton>
      </FormButtonGroup>
    </DialogBox>
  </form>
</template>
