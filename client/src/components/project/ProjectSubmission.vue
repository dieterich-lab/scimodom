<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { HTTPSecure } from '@/services/API'

const router = useRouter()
const props = defineProps(['projectForm'])
const message = ref()

const submitForm = () => {
  HTTPSecure.post('/management/project', props.projectForm)
    .then((response) => {
      if (response.status == 200) {
        router.push({ name: 'home' })
      }
    })
    .catch((error) => {
      message.value = error.response.data.message
      console.log(error)
    })
}

const dropForm = () => {
  router.push({ name: 'home' })
}
</script>

<template>
  <SectionLayout>
    <div>
      <div class="flex flex-col mx-auto">
        <div class="text-center -mt-4 mb-4 text-xl font-semibold dark:text-white/80">
          Project submission
        </div>
      </div>
      <h3 class="mt-0 mb-4 dark:text-white/80">
        Click <span class="inline font-semibold">"Submit"</span> to send a project request. A
        notification will be sent to your email address as soon as the project is created. Click
        <span class="inline font-semibold">"Cancel"</span> to drop the request. In the latter case,
        all information that you entered will be lost.
      </h3>
      <div v-if="message" class="flex m-4 justify-center">
        <Message severity="error" :closable="false">{{ message }}</Message>
      </div>
      <div class="flex flow-row justify-center gap-4">
        <Button label="Submit" size="large" @click="submitForm" />
        <Button label="Cancel" size="large" severity="danger" @click="dropForm" />
      </div>
    </div>
  </SectionLayout>
</template>
