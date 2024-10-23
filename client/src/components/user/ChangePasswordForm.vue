<script setup lang="ts">
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { HTTP, HTTPSecure } from '@/services/API'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import FormBox from '@/components/ui/FormBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import FormButtonGroup from '@/components/ui/FormButtonGroup.vue'
import FormButton from '@/components/ui/FormButton.vue'
import FormText from '@/components/ui/FormText.vue'
import { PRIMARY_DIALOG_STYLE } from '@/utils/UiStyle'

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

function changePassword(values: FormData) {
  let request
  if (dialogState.token) {
    request = HTTP.post('/user/do_password_reset', {
      email: dialogState.email,
      password: values.password,
      token: dialogState.token
    })
  } else {
    request = HTTPSecure.post('/user/change_password', {
      password: values.password
    })
  }

  request
    .then((response) => {
      if (response.status === 200) {
        dialogState.message = 'Password set successfully.'
        dialogState.state = DIALOG.ALERT
      }
    })
    .catch((err) => {
      dialogState.handle_error(err, 'Something went wrong', {
        state: DIALOG.ALERT
      })
    })
}

function cancel() {
  dialogState.state = DIALOG.NONE
}

const onSubmit = handleSubmit((values: FormData) => {
  changePassword(values)
})
</script>

<template>
  <form @submit="onSubmit">
    <FormBox :ui-style="PRIMARY_DIALOG_STYLE">
      <FormText>Change password for {{ dialogState.email }}:</FormText>
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
      <FormButtonGroup>
        <FormButton type="submit" :ui-style="PRIMARY_DIALOG_STYLE">Change</FormButton>
        <FormButton @on-click="cancel()" :ui-style="PRIMARY_DIALOG_STYLE">Cancel</FormButton>
      </FormButtonGroup>
    </FormBox>
  </form>
</template>
