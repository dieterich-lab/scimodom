<script setup lang="ts">
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP } from '@/services/API'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import DialogBox from '@/components/ui/DialogBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import DialogButtonGroup from '@/components/ui/DialogButtonGroup.vue'
import DialogButton from '@/components/ui/DialogButton.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/ui_style'

interface FormData {
  email: string
}

const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup.string().required('required field').email('invalid email').label('Email address')
})
const { defineField, handleSubmit, errors } = useForm<FormData>({
  validationSchema: validationSchema
})

const [email] = defineField('email')

if (dialogState.email != null) {
  email.value = dialogState.email
}

function requestPasswordReset(values: FormData) {
  HTTP.post('/user/request_password_reset', { email: values.email })
    .then((response) => {
      if (response.status == 200) {
        dialogState.message =
          'We just sent you an email with a link. Please visit the link to set your new password.'
        dialogState.state = DIALOG.ALERT
      }
    })
    .catch((err) => {
      dialogState.handle_error(err, 'Sorry - something went wrong', {
        state: DIALOG.RESET_PASSWORD_REQUEST,
        email: values.email
      })
    })
}

function cancel() {
  dialogState.state = DIALOG.NONE
}

const onSubmit = handleSubmit((values) => {
  requestPasswordReset(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <DialogBox :ui-style="PRIMARY_DIALOG_STYLE">
      <FormTextInput v-model="email" :error="errors.email" :ui-style="PRIMARY_DIALOG_STYLE">
        Email
      </FormTextInput>
      <DialogButtonGroup>
        <DialogButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">
          Request Password Reset
        </DialogButton>
        <DialogButton @on-click="cancel()" :ui-style="PRIMARY_DIALOG_STYLE">Cancel</DialogButton>
      </DialogButtonGroup>
    </DialogBox>
  </form>
</template>
