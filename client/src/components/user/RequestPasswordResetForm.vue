<script setup>
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP } from '@/services'
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import FormBox from '@/components/ui/FormBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'
import FormText from '@/components/ui/FormText.vue'

const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup.string().required('required field').email('invalid email').label('Email address')
})
const { defineField, handleSubmit, errors } = useForm({
  validationSchema: validationSchema
})

const [email] = defineField('email')

if (dialogState.email != null) {
  email.value = dialogState.email
}

function requestPasswordReset(values) {
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
    <FormBox>
      <FormText>{{ dialogState.message }}</FormText>
      <FormTextInput v-model="email" :error="errors.email">Email </FormTextInput>
      <FormButtonGroup>
        <FormButton type="submit">Request Password Reset</FormButton>
        <FormButton @on-click="cancel()">Cancel</FormButton>
      </FormButtonGroup>
    </FormBox>
  </form>
</template>
