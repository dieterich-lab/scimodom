<script setup>
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP } from '@/services'
import { useAccessToken } from '@/utils/AccessToken.js'
import { DIALOG, useDialogState } from '@/utils/DialogState.js'
import FromBox from '@/components/ui/FromBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'

const accessToken = useAccessToken()
const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup.string().required().email().label('Email address')
})
const { defineField, handleSubmit, resetForm, errors } = useForm({
  validationSchema: validationSchema
})

const [email] = defineField('email')
const [password] = defineField('password')

function login(values) {
  HTTP.post('/user/login', { email: values.email, password: values.password })
    .then((response) => {
      if (response.status == 200) {
        accessToken.access_token = response.data.access_token
        dialogState.state = DIALOG.NONE
      }
    })
    .catch((err) => {
      console.log(`Failed to login: ${err.text}`)
      dialogState.$patch({
        state: DIALOG.LOGIN,
        error: 'Failed to login - please try again.',
        email: values.email
      })
    })
}

function cancel() {
  dialogState.state = DIALOG.NONE
}

const onSubmit = handleSubmit((values) => {
  login(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <FromBox>
      <p>{{ dialogState.error }}</p>
      <FormTextInput v-model="email" :error="errors.email"> Email </FormTextInput>
      <FormTextInput v-model="password" :error="errors.password" type="password">
        Password
      </FormTextInput>
      <FormButtonGroup>
        <FormButton type="submit">Login</FormButton>
        <FormButton @on-click="cancel()">Cancel</FormButton>
      </FormButtonGroup>
    </FromBox>
  </form>
</template>
