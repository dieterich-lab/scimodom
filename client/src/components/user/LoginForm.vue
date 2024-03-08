<script setup>
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP } from '@/services'
import { useAccessToken } from '@/utils/AccessToken.js'
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import FormBox from '@/components/ui/FormBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'

const accessToken = useAccessToken()
const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup.string().required('required field').email('invalid email').label('Email address')
})
const { defineField, handleSubmit, errors } = useForm({
  validationSchema: validationSchema
})

const [email] = defineField('email')
const [password] = defineField('password')

if (dialogState.email != null) {
  email.value = dialogState.email
}

function login(values) {
  HTTP.post('/user/login', { email: values.email, password: values.password })
    .then((response) => {
      if (response.status == 200) {
        accessToken.access_token = response.data.access_token
        dialogState.state = DIALOG.NONE
      }
    })
    .catch((err) => {
      dialogState.handle_error(err, 'Failed to login - please try again.', {
        state: DIALOG.LOGIN,
        email: values.email
      })
    })
}

function cancel() {
  dialogState.state = DIALOG.NONE
}

function reset_password() {
  dialogState.email = email.value
  dialogState.state = DIALOG.RESET_PASSWORD_REQUEST
}

const onSubmit = handleSubmit((values) => {
  login(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <FormBox>
      <p>{{ dialogState.message }}</p>
      <FormTextInput v-model="email" :error="errors.email">Email </FormTextInput>
      <FormTextInput v-model="password" :error="errors.password" type="password">
        Password
      </FormTextInput>
      <FormButtonGroup>
        <FormButton type="submit">Login</FormButton>
        <FormButton @on-click="cancel()">Cancel</FormButton>
        <FormButton @on-click="reset_password()">Reset Password</FormButton>
      </FormButtonGroup>
    </FormBox>
  </form>
</template>
