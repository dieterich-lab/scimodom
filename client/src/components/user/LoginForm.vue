<script setup lang="ts">
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { useAccessToken } from '@/stores/AccessToken.js'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import DialogBox from '@/components/ui/DialogBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import DialogButtonGroup from '@/components/ui/DialogButtonGroup.vue'
import DialogButton from '@/components/ui/DialogButton.vue'
import DialogText from '@/components/ui/DialogText.vue'
import FormLink from '@/components/ui/FormLink.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/ui_style'
import { login } from '@/services/user'
import { trashRequestErrors } from '@/services/API'

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

function cancel() {
  dialogState.state = DIALOG.NONE
}

function resetPassword() {
  dialogState.email = email.value
  dialogState.state = DIALOG.RESET_PASSWORD_REQUEST
  dialogState.message = null
}

const onSubmit = handleSubmit((values) => {
  login(values.email, values.password, accessToken, dialogState).catch((e) => trashRequestErrors(e))
})
</script>

<template>
  <form @submit="onSubmit">
    <DialogBox :ui-style="PRIMARY_DIALOG_STYLE">
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
      <DialogButtonGroup>
        <DialogButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">Login</DialogButton>
        <DialogButton @on-click="cancel()" :ui-style="PRIMARY_DIALOG_STYLE">Cancel</DialogButton>
      </DialogButtonGroup>
      <div class="flex items-center gap-4">
        <DialogText>Forgot your password?</DialogText>
        <FormLink @click="resetPassword()"> Request a password reset </FormLink>
      </div>
    </DialogBox>
  </form>
</template>
