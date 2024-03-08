<script setup>
import { ref } from 'vue'
import { useAccessToken } from '@/utils/AccessToken.js'
import { HTTPSecure } from '@/services'

const accessToken = useAccessToken()

// cannot call accessToken.get() if not defined this results in error...
const headers = { Authorization: `Bearer ${accessToken.access_token}` }
// there must be a nicer way to set the Authorization directly using the HTTPSecure config
// does this overwrite the config?
// passing headers with null token results in 422 'Not enough segments'...

const user = ref()

const testlogin = () => {
  HTTPSecure.get('/access/testlogin', { headers })
    .then((response) => {
      user.value = response.data
    })
    .catch((err) => {
      console.log(err.response.status)
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
