<script setup lang="ts">
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import DialogBox from '@/components/ui/DialogBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import DialogButtonGroup from '@/components/ui/DialogButtonGroup.vue'
import DialogButton from '@/components/ui/DialogButton.vue'
import DialogText from '@/components/ui/DialogText.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/ui_style'
import { changePassword, resetPassword } from '@/services/user'
import { trashRequestErrors } from '@/services/API'

interface FormData {
  password: string
  passwordConfirm: string
}

const dialogState = useDialogState()

const validationSchema = yup.object({
  password: yup.string().required('required field').min(8, 'min 8 characters').label('Password'),
  passwordConfirm: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('required field')
    .label('Password confirmation')
})
const { defineField, handleSubmit, errors } = useForm<FormData>({
  validationSchema: validationSchema
})

const [password] = defineField('password')
const [passwordConfirm] = defineField('passwordConfirm')

function cancel() {
  dialogState.state = DIALOG.NONE
}

const onSubmit = handleSubmit((values: FormData) => {
  if (dialogState.token && dialogState.email) {
    resetPassword(dialogState.email, values.password, dialogState.token, dialogState).catch((e) =>
      trashRequestErrors(e)
    )
  } else {
    changePassword(values.password, dialogState).catch((e) => trashRequestErrors(e))
  }
})
</script>
<template>
  <form @submit="onSubmit">
    <DialogBox :ui-style="PRIMARY_DIALOG_STYLE">
      <DialogText>Change password for {{ dialogState.email }}:</DialogText>
      <FormTextInput
        v-model="password"
        :error="errors.password"
        type="password"
        :ui-style="PRIMARY_DIALOG_STYLE"
      >
        Password
      </FormTextInput>
      <FormTextInput
        v-model="passwordConfirm"
        :error="errors.passwordConfirm"
        type="password"
        :ui-style="PRIMARY_DIALOG_STYLE"
      >
        Password Confirmation
      </FormTextInput>
      <DialogButtonGroup>
        <DialogButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">Change</DialogButton>
        <DialogButton @on-click="cancel()" :ui-style="PRIMARY_DIALOG_STYLE">Cancel</DialogButton>
      </DialogButtonGroup>
    </DialogBox>
  </form>
</template>
