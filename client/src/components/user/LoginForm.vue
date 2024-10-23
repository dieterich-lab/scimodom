<script setup lang="ts">
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP, prepareAPI } from '@/services/API'
import { useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import FormBox from '@/components/ui/FormBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'
import FormText from '@/components/ui/FormText.vue'
import FormLink from '@/components/ui/FormLink.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/UiStyle'

interface FormData {
  email: string
  password: string
}

const accessToken = useAccessToken()
const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup
    .string()
    .required('Email is required!')
    .email('Invalid email!')
    .max(320, 'At most 320 characters allowed!')
    .label('Email address'),
  password: yup.string().required('Password is required!').label('Password')
})
const { defineField, handleSubmit, errors } = useForm<FormData>({
  validationSchema: validationSchema
})

const [email] = defineField('email')
const [password] = defineField('password')

if (dialogState.email != null) {
  email.value = dialogState.email
}

function login(values: FormData) {
  HTTP.post('/user/login', { email: values.email, password: values.password })
    .then((response) => {
      if (response.status == 200) {
        accessToken.set(values.email, response.data.access_token)
        dialogState.state = DIALOG.NONE
        prepareAPI(false)
      }
    })
    .catch((err) => {
      dialogState.handle_error(err, 'Failed to login - please try again', {
        state: DIALOG.LOGIN,
        email: values.email
      })
    })
}

function cancel() {
  dialogState.state = DIALOG.NONE
}

function resetPassword() {
  dialogState.email = email.value
  dialogState.state = DIALOG.RESET_PASSWORD_REQUEST
  dialogState.message = null
}

const onSubmit = handleSubmit((values) => {
  login(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <FormBox :ui-style="PRIMARY_DIALOG_STYLE">
      <FormTextInput v-model="email" :error="errors.email" :ui-style="PRIMARY_DIALOG_STYLE">
        Email
      </FormTextInput>
      <FormTextInput
        v-model="password"
        :error="errors.password"
        type="password"
        :ui-style="PRIMARY_DIALOG_STYLE"
      >
        Password
      </FormTextInput>
      <FormButtonGroup>
        <FormButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">Login</FormButton>
        <FormButton @on-click="cancel()" :ui-style="PRIMARY_DIALOG_STYLE">Cancel</FormButton>
      </FormButtonGroup>
      <div class="flex items-center gap-4">
        <FormText>Forgot your password?</FormText>
        <FormLink @click="resetPassword()"> Request a password reset </FormLink>
      </div>
    </FormBox>
  </form>
</template>
