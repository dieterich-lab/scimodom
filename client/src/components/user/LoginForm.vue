<script setup>
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP } from '@/services'
import { useAccessToken } from '@/utils/access_token.js'
import { DIALOG, useDialogState } from '@/utils/dialogState.js'
import { createFormManager } from '@/utils/FormManager'
import DialogForm from '@/components/ui/DialogForm.vue'
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
  // const values = dialogFrom.value.form.values;
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
  console.log(`Logging in: ${JSON.stringify(values)}`)
  login(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <FormTextInput v-model="email" :error="errors['email']"> Email </FormTextInput>
    <FormTextInput v-model="password" :error="errors.password" type="password">
      Password
    </FormTextInput>
    <FormButtonGroup>
      <FormButton type="submit">Login</FormButton>
      <FormButton @on-click="cancel()">Cancel</FormButton>
    </FormButtonGroup>
  </form>
</template>
<!--<template>-->
<!--    <DialogForm :validation-schema="validationSchema" ref="dialogFrom" :my-submit="onSubmit">-->
<!--        <template v-slot:fields>-->
<!--            <p class="text-primary-900">{{ dialogState.error || '' }}</p>-->
<!--            <FormInput name="email" :model="email" :error="errors.email">-->
<!--                Email-->
<!--            </FormInput>-->
<!--            <FormInput name="password" :model="password" :error="errors.password" type="password">-->
<!--                Password-->
<!--            </FormInput>-->
<!--        </template>-->
<!--        <template v-slot:buttons>-->
<!--            <FormButton type="submit">Login</FormButton>-->
<!--            <FormButton @on-click="cancel()">Cancel</FormButton>-->
<!--        </template>-->
<!--    </DialogForm>-->
<!--</template>-->
