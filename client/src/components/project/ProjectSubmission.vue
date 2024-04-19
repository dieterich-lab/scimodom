<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { HTTPSecure } from '@/services/API'

const router = useRouter()
const props = defineProps(['projectForm'])

const submitForm = () => {
  HTTPSecure.post('/management/project', props.projectForm)
    .then((response) => {
      if (response.status == 200) {
        router.push({ name: 'home' })
      }
    })
    .catch((error) => {
      return {
        status: error.response ? error.response.status : 0,
        data: {},
        error: error.message
      }
      // on error what to do next?
    })
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
        The project form has been successfully validated. Click
        <span class="inline font-semibold">"Submit"</span> to finalise the submission. A
        notification will be sent to your email address as soon as the project is created.
      </h3>
      <div class="flex justify-center">
        <Button label="Submit" size="large" @click="submitForm" />
      </div>
    </div>
  </SectionLayout>
</template>
