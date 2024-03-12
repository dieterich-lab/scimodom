<script setup>
import { ref } from 'vue'
import { HTTPSecure } from '@/services/API'

const user = ref()

const testlogin = () => {
  HTTPSecure.get('/access/testlogin')
    .then((response) => {
      user.value = response.data
    })
    .catch((err) => {
      // console.log(err.response.status)
      console.log(err)
      // on error what to do
    })
}
</script>

<template>
  <DefaultLayout>
    <SectionLayout>
      <h1
        class="font-ham mb-4 text-3xl font-extrabold text-gray-900 dark:text-white/80 md:text-5xl lg:text-6xl"
      >
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-gg-2 from-10% via-gg-1 via-40% via-gb-2 via-60% to-gb-4 to-100"
        >
          User
        </span>
        account
      </h1>
      <p class="text-lg font-normal text-gray-500 dark:text-surface-400 lg:text-xl">
        Manage settings
      </p>
      <Divider />

      <div class="flex">
        <Button
          @click="testlogin()"
          type="button"
          size="small"
          icon="pi pi-eye"
          label="Check it!"
        />
      </div>
      <div class="mt-4">
        <p>USER IS : {{ user }}</p>
      </div>
    </SectionLayout>
  </DefaultLayout>
</template>
