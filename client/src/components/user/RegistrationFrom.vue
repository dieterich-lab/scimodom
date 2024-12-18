<script setup lang="ts">
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { DIALOG, useDialogState } from '@/stores/DialogState.js'
import { SECONDARY_STYLE } from '@/utils/ui_style'
import DialogBox from '@/components/ui/DialogBox.vue'
import FormTextInput from '@/components/ui/FormTextInput.vue'
import DialogButtonGroup from '@/components/ui/DialogButtonGroup.vue'
import DialogButton from '@/components/ui/DialogButton.vue'
import { registerUser } from '@/services/user'
import { trashRequestErrors } from '@/services/API'

interface FormData {
  email: string
  password: string
  passwordConfirm: string
}

const dialogState = useDialogState()

const validationSchema = yup.object({
  email: yup
    .string()
    .required('Email is required!')
    .email('Invalid email!')
    .max(320, 'At most 320 characters allowed!')
    .label('Email address'),
  password: yup
    .string()
    .required('Password is required!')
    .min(8, 'min 8 characters')
    .label('Password'),
  passwordConfirm: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords must match!')
    .required('Password is required!')
    .label('Password confirmation')
})
const { defineField, handleSubmit, errors } = useForm<FormData>({
  validationSchema: validationSchema
})

const [email] = defineField('email')
const [password] = defineField('password')
const [passwordConfirm] = defineField('passwordConfirm')

function cancel() {
  dialogState.state = DIALOG.NONE
}

const onSubmit = handleSubmit((values) => {
  registerUser(values.email, values.password, dialogState).catch((e) => trashRequestErrors(e))
})
</script>

<template>
  <form @submit="onSubmit">
    <DialogBox :ui-style="SECONDARY_STYLE">
      <FormTextInput v-model="email" :error="errors.email" :ui-style="SECONDARY_STYLE">
        Email
      </FormTextInput>
      <FormTextInput
        v-model="password"
        :error="errors.password"
        type="password"
        :ui-style="SECONDARY_STYLE"
      >
        Password
      </FormTextInput>
      <FormTextInput
        v-model="passwordConfirm"
        :error="errors.passwordConfirm"
        type="password"
        :ui-style="SECONDARY_STYLE"
      >
        Password Confirmation
      </FormTextInput>
      <DialogButtonGroup>
        <DialogButton type="submit" :ui-style="SECONDARY_STYLE">Sign Up</DialogButton>
        <DialogButton @on-click="cancel()" :ui-style="SECONDARY_STYLE">Cancel</DialogButton>
      </DialogButtonGroup>
    </DialogBox>
  </form>
</template>
