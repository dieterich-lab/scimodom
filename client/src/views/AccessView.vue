<script setup>
import { ref } from 'vue'
import { HTTPSecure } from '@/services'

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
