<script setup>
import { ref } from 'vue'
import { Form } from 'vee-validate'
import * as yup from 'yup'

// import { HTTPSecure } from '@/services'
import { HTTP } from '@/services'

import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'
import FormInput from '@/components/ui/FormInput.vue'

import axios from 'axios'
const enabled = ref(false)

// keep validation for sign-up, then we can leave it w/o validation for sign-in
// but required must stay
const schema = yup.object({
  email: yup.string().required('Email required').email('Invalid email'),
  password: yup.string().required('Password required').min(8, 'Min. 8 characters')
})

// handleSubmit, submitForm?
// for login now we don't use HTTPSecure, just the normal
const onSubmit = (values) => {
  HTTP.post('/login', { username: values.email, password: values.password })
    .then((res) => {
      console.log(res)
      enabled.value = false
    })
    .catch((err) => {
      console.log(err)
    })
}
</script>

<template>
  <header
    class="top-0 z-20 sticky bg-white opacity-90 border-b border-surface-200 dark:bg-surface-900 dark:opacity-100 dark:border-surface-800"
  >
    <div
      class="p-1 bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100%"
    />
    <div class="mx-auto w-full max-w-screen-2xl p-2 py-6 lg:py-8 flex flex-wrap items-center">
      <div class="flex flex-wrap 2xl:w-4/5 xl:w-auto">
        <ScimodomLogo />
        <NavigationBar />
      </div>
      <!-- login -->
      <div class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0 gap-4">
        <Button icon="pi pi-user" size="small" label="Login" raised @click="enabled = true" />
        <Button icon="pi pi-user-plus" size="small" label="Sign Up" severity="secondary" raised />
        <!-- visible when button is toggled -->
        <Dialog
          v-model:visible="enabled"
          modal
          :pt="{
            root: 'border-none',
            mask: {
              style: 'backdrop-filter: blur(2px)'
            }
          }"
        >
          <template #container="{ closeCallback }">
            <Form @submit="onSubmit" :validation-schema="schema">
              <div
                class="flex flex-col px-8 py-8 gap-4"
                style="
                  border-radius: 12px;
                  background-image: radial-gradient(
                    circle at center,
                    rgb(var(--primary-600)),
                    rgb(var(--primary-500)),
                    rgb(var(--primary-400))
                  );
                "
              >
                <div class="inline-flex flex-col gap-2">
                  <label for="username" class="text-primary-50 font-semibold">Username</label>
                  <FormInput input="email" type="text" />
                </div>
                <div class="inline-flex flex-col gap-2">
                  <label for="password" class="text-primary-50 font-semibold">Password</label>
                  <FormInput input="password" />
                </div>
                <div class="flex items-center gap-4">
                  <!-- PrimeVue Button not working? closeCallback cannot be invoked on click -->
                  <button
                    class="relative px-2.5 py-1.5 min-w-[2rem] items-center justify-center inline-flex rounded-md font-semibold text-center align-bottom text-sm text-white dark:text-surface-900 bg-primary-500 dark:bg-primary-400 ring-1 ring-primary-500 dark:ring-primary-400 hover:bg-primary-600 dark:hover:bg-primary-300 hover:ring-primary-600 dark:hover:ring-primary-300 focus:ring-offset-2 focus:ring-primary-500 dark:focus:ring-primary-400 p-4 w-full border border-white-alpha-30"
                  >
                    Sign-In
                  </button>
                  <Button
                    label="Cancel"
                    @click="closeCallback"
                    class="p-4 w-full text-primary-50 border border-white-alpha-30"
                  ></Button>
                </div>
              </div>
            </Form>
          </template>
        </Dialog>
      </div>
    </div>
  </header>
</template>
