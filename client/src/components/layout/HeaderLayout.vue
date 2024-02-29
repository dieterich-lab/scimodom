<script setup>
import ScimodomLogo from './ScimodomLogo.vue'
import NavigationBar from './NavigationBar.vue'

import { ref } from 'vue'
const enabled = ref(false)
const username = ref()
const password = ref()

const login = () => {
  console.log('LOGIN', username.value, password.value)
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
      <div class="flex flex-wrap 2xl:w-1/5 xl:w-auto 2xl:pl-8 xl:pl-0 gap-4">
        <Button icon="pi pi-user" size="small" label="Login" raised @click="enabled = true" />
        <Button icon="pi pi-user-plus" size="small" label="Sign Up" severity="secondary" raised />
        <Dialog
          v-model:visible="enabled"
          modal
          :pt="{
            mask: {
              style: 'backdrop-filter: blur(2px)'
            }
          }"
        >
          <template #container="{ closeCallback }">
            <form @submit="login">
              <div
                class="flex flex-col px-10 py-7 gap-5"
                style="
                  border-radius: 12px;
                  background-image: radial-gradient(
                    circle at center,
                    rgb(var(--primary-500)),
                    rgb(var(--primary-600)),
                    rgb(var(--primary-700))
                  );
                "
              >
                <div class="inline-flex flex-col gap-2">
                  <label for="username" class="text-primary-50 font-semibold">Username</label>
                  <InputText
                    id="username"
                    v-model="username"
                    class="bg-white/20 border-0 p-4 text-primary-50"
                  ></InputText>
                </div>
                <div class="inline-flex flex-col gap-2">
                  <label for="password" class="text-primary-50 font-semibold">Password</label>
                  <InputText
                    id="password"
                    v-model="password"
                    class="bg-white/20 border-0 p-4 text-primary-50"
                    type="password"
                  ></InputText>
                </div>
                <div class="flex items-center gap-2">
                  <Button
                    label="Sign-In"
                    @click="closeCallback"
                    class="p-4 w-full border border-white-alpha-30"
                  ></Button>
                  <Button
                    label="Cancel"
                    @click="closeCallback"
                    class="p-4 w-full text-primary-50 border border-white-alpha-30"
                  ></Button>
                </div>
              </div>
            </form>
          </template>
        </Dialog>
      </div>
      <!-- <SearchForm /> -->
    </div>
  </header>
</template>
