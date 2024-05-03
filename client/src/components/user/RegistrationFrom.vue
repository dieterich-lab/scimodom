<script setup>
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP } from '@/services/API'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import SecondaryStyle from '@/ui_styles/SecondaryDialogStyle.js'
import FromBox from '@/components/ui/FormBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'

const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup
    .string()
    .required('required field')
    .email('not a valid address')
    .label('Email address'),
  password: yup.string().required('required field').min(8, 'min 8 characters').label('Password'),
  passwordConfirm: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('required field')
    .label('Password confirmation')
})
const { defineField, handleSubmit, resetForm, errors } = useForm({
  validationSchema: validationSchema
})

const [email] = defineField('email')
const [password] = defineField('password')
const [passwordConfirm] = defineField('passwordConfirm')

function register(values) {
  HTTP.post('/user/register_user', { email: values.email, password: values.password })
    .then((response) => {
      if (response.status == 200) {
        dialogState.message =
          'We just sent you an email with a link to confirm your address. Please use the link to complete the registration.'
        dialogState.state = DIALOG.ALERT
      }
    })
    .catch((err) => {
      dialogState.handle_error(err, 'Failed to register', {
        state: DIALOG.REGISTER_ENTER_DATA,
        email: values.email
      })
    })
}

function cancel() {
  dialogState.state = DIALOG.NONE
}

const onSubmit = handleSubmit((values) => {
  register(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <FromBox :ui-style="SecondaryStyle">
      <FormTextInput v-model="email" :error="errors.email" :ui-style="SecondaryStyle">
        Email
      </FormTextInput>
      <FormTextInput
        v-model="password"
        :error="errors.password"
        type="password"
        :ui-style="SecondaryStyle"
      >
        Password
      </FormTextInput>
      <FormTextInput
        v-model="passwordConfirm"
        :error="errors.passwordConfirm"
        type="password"
        :ui-style="SecondaryStyle"
      >
        Password Confirmation
      </FormTextInput>
      <FormButtonGroup>
        <FormButton type="submit" :ui-style="SecondaryStyle">Sign Up</FormButton>
        <FormButton @on-click="cancel()" :ui-style="SecondaryStyle">Cancel</FormButton>
      </FormButtonGroup>
    </FromBox>
  </form>
</template>
